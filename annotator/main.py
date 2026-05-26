"""
로컬 이미지 박스 어노테이션 서버.

저장 레이아웃: works/{work_id}/ (annotator/storage_layout.py 참고)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from PIL import Image

try:
    from .storage_layout import (
        ALLOWED_EXT,
        AnnotMode,
        AppMode,
        FUNCTION_TAG_DEPTH,
        MODE_CHILD_LAYER,
        MODE_CROP_OUTPUT,
        MODE_SOURCE_LABEL,
        MODE_SOURCE_LAYER,
        TagMode,
        build_code_tag_payload,
        build_crop_payload,
        build_function_tag_payload,
        build_catalog_payload,
        catalog_is_complete,
        catalog_path,
        code_tag_path,
        crop_meta_path,
        crop_output_dir,
        function_tag_path,
        images_dir,
        is_catalog_mode,
        is_function_tag_mode,
        list_catalog_works,
        list_images,
        read_catalog,
        resolve_image,
        resolve_work_pdf,
        source_layer,
    )
except ImportError:
    from storage_layout import (
        ALLOWED_EXT,
        AnnotMode,
        AppMode,
        FUNCTION_TAG_DEPTH,
        MODE_CHILD_LAYER,
        MODE_CROP_OUTPUT,
        MODE_SOURCE_LABEL,
        MODE_SOURCE_LAYER,
        TagMode,
        build_code_tag_payload,
        build_crop_payload,
        build_function_tag_payload,
        build_catalog_payload,
        catalog_is_complete,
        catalog_path,
        code_tag_path,
        crop_meta_path,
        crop_output_dir,
        function_tag_path,
        images_dir,
        is_catalog_mode,
        is_function_tag_mode,
        list_catalog_works,
        list_images,
        read_catalog,
        resolve_image,
        resolve_work_pdf,
        source_layer,
    )

try:
    from .pdf_import import import_work_pdf
except ImportError:
    from pdf_import import import_work_pdf

STATIC_DIR = Path(__file__).resolve().parent / "static"
PROJECT_ROOT = Path(__file__).resolve().parent.parent

MODE_PAGE_STAFF: AnnotMode = "page_staff"
MODE_STAFF_MEASURE: AnnotMode = "staff_measure"
MODE_MEASURE_NOTE: AnnotMode = "measure_note"
MODE_FUNCTION_IN_PAGE: AnnotMode = "function_in_page"
MODE_FUNCTION_IN_STAFF: AnnotMode = "function_in_staff"
MODE_FUNCTION_IN_MEASURE: AnnotMode = "function_in_measure"
MODE_FUNCTION_IN_NOTE: AnnotMode = "function_in_note"

app = FastAPI(title="Local Box Annotator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class Box(BaseModel):
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    w: int = Field(gt=0)
    h: int = Field(gt=0)


class SubmitBody(BaseModel):
    mode: AnnotMode = MODE_PAGE_STAFF
    relative_path: str
    boxes: list[Box]


class TagBody(BaseModel):
    mode: TagMode
    relative_path: str
    code: str = ""
    tag: str = ""


class CatalogBody(BaseModel):
    work: str
    title: str = ""
    subtitle: str = ""
    display_title: str = ""
    composer: str = ""
    display_composer: str = ""
    copyright_free: bool | None = None
    analysis: str = ""


def _write_json_file(path: Path, data: dict[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        f.write("\n")
    return path.relative_to(PROJECT_ROOT).as_posix()


def _resolve_source(mode: AppMode, rel: str) -> Path:
    try:
        candidate = resolve_image(mode, rel)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if not candidate.is_file():
        raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다.")
    if candidate.suffix.lower() not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail="지원하지 않는 이미지 형식입니다.")
    return candidate


def _image_context(src: Path) -> tuple[str, Path]:
    rel = src.relative_to(PROJECT_ROOT / "works")
    work = rel.parts[0]
    under = Path(*rel.parts[3:])
    return work, under


def _sort_boxes_reading_order(boxes: list[Box]) -> list[Box]:
    return sorted(boxes, key=lambda b: (b.y, b.x))


def _clamp_crop_rect(b: Box, iw: int, ih: int, idx: int) -> tuple[int, int, int, int]:
    x2 = min(b.x + b.w, iw)
    y2 = min(b.y + b.h, ih)
    x1 = max(0, min(b.x, iw - 1))
    y1 = max(0, min(b.y, ih - 1))
    if x2 <= x1 or y2 <= y1:
        raise HTTPException(
            status_code=400,
            detail=f"박스 {idx}가 이미지 범위 밖이거나 크기가 0입니다.",
        )
    return x1, y1, x2, y2


def _crop_position(x1: int, y1: int, x2: int, y2: int) -> dict[str, int]:
    return {"top": y1, "left": x1, "width": x2 - x1, "height": y2 - y1}


def _child_name(mode: AnnotMode, idx: int) -> str:
    layer = MODE_CHILD_LAYER[mode]
    singular = layer[:-1] if layer.endswith("s") else layer
    return f"{singular}_{idx:03d}"


def _tag_json_path(mode: TagMode, src: Path) -> Path:
    work, _ = _image_context(src)
    if is_function_tag_mode(mode):
        rel = src.relative_to(images_dir(work, "functions"))
        expected = FUNCTION_TAG_DEPTH[mode]
        if len(rel.parts) != expected:
            raise HTTPException(
                status_code=400,
                detail=f"function 이미지 경로는 {expected}단계여야 합니다.",
            )
        return function_tag_path(work, rel)

    layer = source_layer(mode)
    rel = src.relative_to(images_dir(work, layer))
    return code_tag_path(work, layer, rel)


def _read_tag_field(path: Path, field: str) -> str:
    if not path.is_file():
        return ""
    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return ""
    if isinstance(data, dict) and isinstance(data.get(field), str):
        return data[field]
    return ""


@app.get("/api/images")
def api_list_images(mode: AppMode = MODE_PAGE_STAFF):
    if is_catalog_mode(mode):
        works = list_catalog_works()
        complete_map = {work: catalog_is_complete(read_catalog(work)) for work in works}
        return {
            "images": works,
            "mode": mode,
            "source_label": MODE_SOURCE_LABEL.get(mode, ""),
            "catalog_complete": complete_map,
        }
    return {
        "images": list_images(mode),
        "mode": mode,
        "source_label": MODE_SOURCE_LABEL.get(mode, ""),
    }


@app.get("/api/work-pdf/{work_id}")
def get_work_pdf(work_id: str):
    try:
        pdf = resolve_work_pdf(work_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return FileResponse(pdf, media_type="application/pdf")


@app.get("/api/catalog")
def get_catalog(work: str):
    if not work or work.startswith("_"):
        raise HTTPException(status_code=400, detail="유효하지 않은 work입니다.")
    data = read_catalog(work)
    ti = data["music_info"]["title_info"]
    ci = data["music_info"]["composer_info"]
    cf = data["copyright_info"]["copyright_free"]
    return {
        "ok": True,
        "work": work,
        "title": ti["title"],
        "subtitle": ti["subtitle"],
        "display_title": ti["display_title"],
        "composer": ci["composer"],
        "display_composer": ci["display_composer"],
        "copyright_free": cf,
        "analysis": data["analysis_info"]["content"],
        "complete": catalog_is_complete(data),
        "catalog_path": catalog_path(work).relative_to(PROJECT_ROOT).as_posix(),
        "pdf_path": data.get("pdf", ""),
    }


@app.post("/api/catalog")
def save_catalog(body: CatalogBody):
    work = body.work.strip()
    if not work or work.startswith("_"):
        raise HTTPException(status_code=400, detail="유효하지 않은 work입니다.")
    payload = build_catalog_payload(body.model_dump(), work)
    written = _write_json_file(catalog_path(work), payload)
    complete = catalog_is_complete(payload)
    return {"ok": True, "catalog_path": written, "complete": complete}


@app.get("/api/image/{full_path:path}")
def get_image(full_path: str, mode: AppMode = MODE_PAGE_STAFF):
    return FileResponse(_resolve_source(mode, full_path))


def _submit_crop(mode: AnnotMode, src: Path, ordered: list[Box]) -> tuple[list[str], str]:
    im = Image.open(src).convert("RGB")
    iw, ih = im.size
    work, source_under = _image_context(src)
    source_layer_name = MODE_SOURCE_LAYER[mode]
    output_layer = MODE_CROP_OUTPUT[mode]
    child_layer = MODE_CHILD_LAYER[mode]

    dest_parent = source_under.parent if source_under.parent != Path(".") else Path()
    dest_dir = crop_output_dir(work, output_layer, dest_parent / src.stem)
    dest_dir.mkdir(parents=True, exist_ok=True)

    saved: list[str] = []
    items: list[dict[str, Any]] = []
    for idx, b in enumerate(ordered, start=1):
        x1, y1, x2, y2 = _clamp_crop_rect(b, iw, ih, idx)
        name = _child_name(mode, idx)
        crop = im.crop((x1, y1, x2, y2))
        out_path = dest_dir / f"{name}.jpg"
        crop.save(out_path, format="JPEG", quality=92)
        saved.append(out_path.relative_to(PROJECT_ROOT).as_posix())
        items.append(
            {
                "index": idx,
                "name": name,
                "position": _crop_position(x1, y1, x2, y2),
            }
        )

    meta = crop_meta_path(work, output_layer, source_layer_name, source_under)
    payload = build_crop_payload(work, source_layer_name, source_under, child_layer, items)
    meta_written = _write_json_file(meta, payload)
    return saved, meta_written


_SUBMIT_HANDLERS = {
    MODE_PAGE_STAFF: _submit_crop,
    MODE_STAFF_MEASURE: _submit_crop,
    MODE_MEASURE_NOTE: _submit_crop,
    MODE_FUNCTION_IN_PAGE: _submit_crop,
    MODE_FUNCTION_IN_STAFF: _submit_crop,
    MODE_FUNCTION_IN_MEASURE: _submit_crop,
    MODE_FUNCTION_IN_NOTE: _submit_crop,
}


@app.get("/api/tag")
def get_tag(mode: TagMode, relative_path: str):
    src = _resolve_source(mode, relative_path)
    tag_path = _tag_json_path(mode, src)
    field = "tag" if is_function_tag_mode(mode) else "code"
    return {
        "ok": True,
        "mode": mode,
        "field": field,
        field: _read_tag_field(tag_path, field),
        "tag_path": tag_path.relative_to(PROJECT_ROOT).as_posix(),
    }


@app.post("/api/tag")
def save_tag(body: TagBody):
    src = _resolve_source(body.mode, body.relative_path)
    work, _ = _image_context(src)
    tag_path = _tag_json_path(body.mode, src)

    if is_function_tag_mode(body.mode):
        fn_rel = src.relative_to(images_dir(work, "functions"))
        payload = build_function_tag_payload(work, fn_rel, body.tag)
    else:
        layer = source_layer(body.mode)
        rel = src.relative_to(images_dir(work, layer))
        payload = build_code_tag_payload(work, layer, rel, body.code)

    written = _write_json_file(tag_path, payload)
    return {"ok": True, "mode": body.mode, "tag_path": written}


@app.post("/api/submit")
def submit(body: SubmitBody):
    src = _resolve_source(body.mode, body.relative_path)
    ordered = _sort_boxes_reading_order(body.boxes)
    handler = _SUBMIT_HANDLERS.get(body.mode)
    if handler is None:
        raise HTTPException(status_code=400, detail="알 수 없는 mode입니다.")
    try:
        saved, metadata = handler(body.mode, src, ordered)
    except OSError as e:
        raise HTTPException(status_code=400, detail=f"이미지를 열거나 저장할 수 없습니다: {e}") from e
    return {
        "ok": True,
        "saved": saved,
        "metadata": metadata,
        "count": len(saved),
        "mode": body.mode,
    }


@app.post("/api/work-upload")
async def upload_work_pdf(work: str = Form(...), file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="PDF 파일만 업로드할 수 있습니다.")
    pdf_bytes = await file.read()
    try:
        result = import_work_pdf(work, pdf_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except OSError as e:
        raise HTTPException(status_code=400, detail=f"파일 저장에 실패했습니다: {e}") from e
    return {"ok": True, **result}


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

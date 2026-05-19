"""
로컬 이미지 박스 어노테이션 서버.
모드별로 다른 소스 디렉터리와 저장 경로를 사용합니다.

- page_staff: source/pages → source/staffs/{악보}/{페이지stem}/staff_NNN.jpg
  + data/position_data/staffs_in_page/{악보}/{페이지stem}.json
- staff_measure: source/staffs → source/measures/{...}/{staffstem}/measure_NNN.jpg
  + data/position_data/measures_in_staff/{악보}/{페이지}/{staffstem}.json
- measure_note: source/measures → source/notes/{...}/{measurestem}/note_NNN.jpg
  + data/position_data/notes_in_measure/{악보}/{페이지}/{staff}/{measurestem}.json
- function_in_page: source/pages → source/functions/pages/{악보}/{페이지}/function_NNN.jpg
  + data/position_data/functions_in_page/{악보}/{페이지}.json
- function_in_staff: source/staffs → source/functions/pages/{...}/{staff}/function_NNN.jpg
  + data/position_data/functions_in_staff/{악보}/{페이지}/{staff}.json
- function_in_measure: source/measures → source/functions/pages/{...}/{measure}/function_NNN.jpg
  + data/position_data/functions_in_measure/{악보}/{페이지}/{staff}/{measure}.json
- function_in_note: source/notes → source/functions/pages/{...}/{note}/function_NNN.jpg
  + data/position_data/function_in_note/{악보}/{페이지}/{staff}/{measure}/{note}.json
- code_of_page: source/pages → data/tag_data/pages/{악보}/{페이지}.json
- code_of_staff: source/staffs → data/tag_data/pages/{악보}/{페이지}/{staff}.json
- code_of_measure: source/measures → data/tag_data/pages/{악보}/{페이지}/{staff}/{measure}.json
- code_of_note: source/notes → data/tag_data/pages/{악보}/{페이지}/{staff}/{measure}/{note}.json
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from PIL import Image

STATIC_DIR = Path(__file__).resolve().parent / "static"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PAGES_ROOT = PROJECT_ROOT / "source" / "pages"
STAFFS_ROOT = PROJECT_ROOT / "source" / "staffs"
MEASURES_ROOT = PROJECT_ROOT / "source" / "measures"
NOTES_ROOT = PROJECT_ROOT / "source" / "notes"
FUNCTIONS_PAGES_ROOT = PROJECT_ROOT / "source" / "functions" / "pages"
POSITION_DATA_ROOT = PROJECT_ROOT / "data" / "position_data"
STAFFS_IN_PAGE_ROOT = POSITION_DATA_ROOT / "staffs_in_page"
MEASURES_IN_STAFF_ROOT = POSITION_DATA_ROOT / "measures_in_staff"
NOTES_IN_MEASURE_ROOT = POSITION_DATA_ROOT / "notes_in_measure"
FUNCTIONS_IN_PAGE_ROOT = POSITION_DATA_ROOT / "functions_in_page"
FUNCTIONS_IN_STAFF_ROOT = POSITION_DATA_ROOT / "functions_in_staff"
FUNCTIONS_IN_MEASURE_ROOT = POSITION_DATA_ROOT / "functions_in_measure"
FUNCTION_IN_NOTE_ROOT = POSITION_DATA_ROOT / "function_in_note"
TAG_DATA_PAGES_ROOT = PROJECT_ROOT / "data" / "tag_data" / "pages"

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}

TagMode = Literal["code_of_page", "code_of_staff", "code_of_measure", "code_of_note"]

AnnotMode = Literal[
    "page_staff",
    "staff_measure",
    "measure_note",
    "function_in_page",
    "function_in_staff",
    "function_in_measure",
    "function_in_note",
]

MODE_PAGE_STAFF: AnnotMode = "page_staff"
MODE_STAFF_MEASURE: AnnotMode = "staff_measure"
MODE_MEASURE_NOTE: AnnotMode = "measure_note"
MODE_FUNCTION_IN_PAGE: AnnotMode = "function_in_page"
MODE_FUNCTION_IN_STAFF: AnnotMode = "function_in_staff"
MODE_FUNCTION_IN_MEASURE: AnnotMode = "function_in_measure"
MODE_FUNCTION_IN_NOTE: AnnotMode = "function_in_note"
MODE_CODE_OF_PAGE: TagMode = "code_of_page"
MODE_CODE_OF_STAFF: TagMode = "code_of_staff"
MODE_CODE_OF_MEASURE: TagMode = "code_of_measure"
MODE_CODE_OF_NOTE: TagMode = "code_of_note"

AppMode = AnnotMode | TagMode

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
    """relative_path: 해당 모드 기준 루트 아래 경로, 예: sheet_music_01/page_001.jpg"""

    relative_path: str
    boxes: list[Box]


class TagBody(BaseModel):
    mode: TagMode
    relative_path: str
    code: str = ""


def _source_root(mode: AppMode) -> Path:
    if mode in (MODE_PAGE_STAFF, MODE_FUNCTION_IN_PAGE, MODE_CODE_OF_PAGE):
        return PAGES_ROOT
    if mode in (MODE_STAFF_MEASURE, MODE_FUNCTION_IN_STAFF, MODE_CODE_OF_STAFF):
        return STAFFS_ROOT
    if mode in (MODE_MEASURE_NOTE, MODE_FUNCTION_IN_MEASURE, MODE_CODE_OF_MEASURE):
        return MEASURES_ROOT
    if mode in (MODE_FUNCTION_IN_NOTE, MODE_CODE_OF_NOTE):
        return NOTES_ROOT
    raise HTTPException(status_code=400, detail="알 수 없는 mode입니다.")


def _inside_root(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _resolve_source(mode: AppMode, rel: str) -> Path:
    root = _source_root(mode)
    rel_norm = rel.replace("\\", "/").lstrip("/")
    candidate = (root / rel_norm).resolve()
    if not _inside_root(candidate, root):
        raise HTTPException(status_code=400, detail="경로가 허용 범위를 벗어났습니다.")
    if not candidate.is_file():
        raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다.")
    if candidate.suffix.lower() not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail="지원하지 않는 이미지 형식입니다.")
    return candidate


def _sort_boxes_reading_order(boxes: list[Box]) -> list[Box]:
    """위에서 아래, 같은 줄에서는 왼쪽에서 오른쪽 (좌상단 기준)."""

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


def _write_json_file(path: Path, data: dict[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        f.write("\n")
    return path.relative_to(PROJECT_ROOT).as_posix()


def _write_crop_metadata(path: Path, data: dict[str, Any]) -> str:
    return _write_json_file(path, data)


def _tag_json_path(mode: TagMode, src: Path) -> Path:
    if mode == MODE_CODE_OF_PAGE:
        sheet_music = src.parent.name
        page = src.stem
        return TAG_DATA_PAGES_ROOT / sheet_music / f"{page}.json"

    root = _source_root(mode)
    rel = src.relative_to(root)
    sheet_music = rel.parts[0]

    if mode == MODE_CODE_OF_STAFF:
        if len(rel.parts) < 3:
            raise HTTPException(
                status_code=400,
                detail="staff 이미지 경로는 {악보}/{페이지}/{staff}.jpg 형식이어야 합니다.",
            )
        page, staff = rel.parts[1], src.stem
        return TAG_DATA_PAGES_ROOT / sheet_music / page / f"{staff}.json"

    if mode == MODE_CODE_OF_MEASURE:
        if len(rel.parts) < 4:
            raise HTTPException(
                status_code=400,
                detail="measure 이미지 경로는 {악보}/{페이지}/{staff}/{measure}.jpg 형식이어야 합니다.",
            )
        page, staff, measure = rel.parts[1], rel.parts[2], src.stem
        return TAG_DATA_PAGES_ROOT / sheet_music / page / staff / f"{measure}.json"

    if len(rel.parts) < 5:
        raise HTTPException(
            status_code=400,
            detail="note 이미지 경로는 {악보}/{페이지}/{staff}/{measure}/{note}.jpg 형식이어야 합니다.",
        )
    page, staff, measure, note = rel.parts[1], rel.parts[2], rel.parts[3], src.stem
    return TAG_DATA_PAGES_ROOT / sheet_music / page / staff / measure / f"{note}.json"


def _build_tag_payload(mode: TagMode, src: Path, code: str) -> dict[str, Any]:
    if mode == MODE_CODE_OF_PAGE:
        return {"sheet_music": src.parent.name, "code": code}

    root = _source_root(mode)
    rel = src.relative_to(root)
    sheet_music = rel.parts[0]
    payload: dict[str, Any] = {"sheet_music": sheet_music, "code": code}

    if mode == MODE_CODE_OF_STAFF:
        payload["page"] = rel.parts[1]
        return payload

    if mode == MODE_CODE_OF_MEASURE:
        payload["page"] = rel.parts[1]
        payload["staff"] = rel.parts[2]
        return payload

    payload["page"] = rel.parts[1]
    payload["staff"] = rel.parts[2]
    payload["measure"] = rel.parts[3]
    return payload


def _read_tag_code(path: Path) -> str:
    if not path.is_file():
        return ""
    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return ""
    if isinstance(data, dict) and isinstance(data.get("code"), str):
        return data["code"]
    return ""


def _list_images_under(root: Path) -> list[str]:
    if not root.is_dir():
        return []
    out: list[str] = []
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.suffix.lower() in ALLOWED_EXT:
            out.append(p.relative_to(root).as_posix())
    return out


@app.get("/api/images")
def list_images(mode: AppMode = MODE_PAGE_STAFF):
    root = _source_root(mode)
    return {"images": _list_images_under(root), "mode": mode}


@app.get("/api/image/{full_path:path}")
def get_image(full_path: str, mode: AppMode = MODE_PAGE_STAFF):
    resolved = _resolve_source(mode, full_path)
    return FileResponse(resolved)


def _submit_page_staff(src: Path, ordered: list[Box]) -> tuple[list[str], str]:
    im = Image.open(src).convert("RGB")
    iw, ih = im.size
    sheet_music = src.parent.name
    page = src.stem
    dest_dir = STAFFS_ROOT / sheet_music / page
    dest_dir.mkdir(parents=True, exist_ok=True)

    saved: list[str] = []
    staffs_meta: list[dict[str, Any]] = []
    for idx, b in enumerate(ordered, start=1):
        x1, y1, x2, y2 = _clamp_crop_rect(b, iw, ih, idx)
        name = f"staff_{idx:03d}"
        crop = im.crop((x1, y1, x2, y2))
        out_path = dest_dir / f"{name}.jpg"
        crop.save(out_path, format="JPEG", quality=92)
        saved.append((out_path.relative_to(PROJECT_ROOT)).as_posix())
        staffs_meta.append(
            {
                "index": idx,
                "name": name,
                "position": _crop_position(x1, y1, x2, y2),
            }
        )

    meta_path = _write_crop_metadata(
        STAFFS_IN_PAGE_ROOT / sheet_music / f"{page}.json",
        {"sheet_music": sheet_music, "page": page, "staffs": staffs_meta},
    )
    return saved, meta_path


def _submit_staff_measure(src: Path, ordered: list[Box]) -> tuple[list[str], str]:
    im = Image.open(src).convert("RGB")
    iw, ih = im.size
    rel = src.relative_to(STAFFS_ROOT)
    if len(rel.parts) < 3:
        raise HTTPException(
            status_code=400,
            detail="staff 이미지 경로는 {악보}/{페이지}/{staff}.jpg 형식이어야 합니다.",
        )
    sheet_music, page = rel.parts[0], rel.parts[1]
    staff = src.stem
    dest_dir = MEASURES_ROOT / rel.parent / staff
    dest_dir.mkdir(parents=True, exist_ok=True)

    saved: list[str] = []
    measures_meta: list[dict[str, Any]] = []
    for idx, b in enumerate(ordered, start=1):
        x1, y1, x2, y2 = _clamp_crop_rect(b, iw, ih, idx)
        name = f"measure_{idx:03d}"
        crop = im.crop((x1, y1, x2, y2))
        out_path = dest_dir / f"{name}.jpg"
        crop.save(out_path, format="JPEG", quality=92)
        saved.append((out_path.relative_to(PROJECT_ROOT)).as_posix())
        measures_meta.append(
            {
                "index": idx,
                "name": name,
                "position": _crop_position(x1, y1, x2, y2),
            }
        )

    meta_path = _write_crop_metadata(
        MEASURES_IN_STAFF_ROOT / sheet_music / page / f"{staff}.json",
        {"sheet_music": sheet_music, "staff": staff, "staffs": measures_meta},
    )
    return saved, meta_path


def _submit_measure_note(src: Path, ordered: list[Box]) -> tuple[list[str], str]:
    im = Image.open(src).convert("RGB")
    iw, ih = im.size
    rel = src.relative_to(MEASURES_ROOT)
    if len(rel.parts) < 4:
        raise HTTPException(
            status_code=400,
            detail="measure 이미지 경로는 {악보}/{페이지}/{staff}/{measure}.jpg 형식이어야 합니다.",
        )
    sheet_music = rel.parts[0]
    measure = src.stem
    dest_dir = NOTES_ROOT / rel.parent / measure
    dest_dir.mkdir(parents=True, exist_ok=True)

    saved: list[str] = []
    notes_meta: list[dict[str, Any]] = []
    for idx, b in enumerate(ordered, start=1):
        x1, y1, x2, y2 = _clamp_crop_rect(b, iw, ih, idx)
        name = f"note_{idx:03d}"
        crop = im.crop((x1, y1, x2, y2))
        out_path = dest_dir / f"{name}.jpg"
        crop.save(out_path, format="JPEG", quality=92)
        saved.append((out_path.relative_to(PROJECT_ROOT)).as_posix())
        notes_meta.append(
            {
                "index": idx,
                "name": name,
                "position": _crop_position(x1, y1, x2, y2),
            }
        )

    meta_path = _write_crop_metadata(
        NOTES_IN_MEASURE_ROOT / rel.parent / f"{measure}.json",
        {"sheet_music": sheet_music, "measure": measure, "notes": notes_meta},
    )
    return saved, meta_path


def _submit_functions_crop(
    src: Path,
    ordered: list[Box],
    dest_dir: Path,
    meta_path: Path,
    meta_base: dict[str, Any],
) -> tuple[list[str], str]:
    im = Image.open(src).convert("RGB")
    iw, ih = im.size
    dest_dir.mkdir(parents=True, exist_ok=True)

    saved: list[str] = []
    functions_meta: list[dict[str, Any]] = []
    for idx, b in enumerate(ordered, start=1):
        x1, y1, x2, y2 = _clamp_crop_rect(b, iw, ih, idx)
        name = f"function_{idx:03d}"
        crop = im.crop((x1, y1, x2, y2))
        out_path = dest_dir / f"{name}.jpg"
        crop.save(out_path, format="JPEG", quality=92)
        saved.append((out_path.relative_to(PROJECT_ROOT)).as_posix())
        functions_meta.append(
            {
                "index": idx,
                "name": name,
                "position": _crop_position(x1, y1, x2, y2),
            }
        )

    meta_path_str = _write_crop_metadata(
        meta_path,
        {**meta_base, "functions": functions_meta},
    )
    return saved, meta_path_str


def _submit_function_in_page(src: Path, ordered: list[Box]) -> tuple[list[str], str]:
    sheet_music = src.parent.name
    page = src.stem
    return _submit_functions_crop(
        src,
        ordered,
        FUNCTIONS_PAGES_ROOT / sheet_music / page,
        FUNCTIONS_IN_PAGE_ROOT / sheet_music / f"{page}.json",
        {"sheet_music": sheet_music, "page": page},
    )


def _submit_function_in_staff(src: Path, ordered: list[Box]) -> tuple[list[str], str]:
    rel = src.relative_to(STAFFS_ROOT)
    if len(rel.parts) < 3:
        raise HTTPException(
            status_code=400,
            detail="staff 이미지 경로는 {악보}/{페이지}/{staff}.jpg 형식이어야 합니다.",
        )
    sheet_music, page = rel.parts[0], rel.parts[1]
    staff = src.stem
    return _submit_functions_crop(
        src,
        ordered,
        FUNCTIONS_PAGES_ROOT / sheet_music / page / staff,
        FUNCTIONS_IN_STAFF_ROOT / sheet_music / page / f"{staff}.json",
        {"sheet_music": sheet_music, "staff": staff},
    )


def _submit_function_in_measure(src: Path, ordered: list[Box]) -> tuple[list[str], str]:
    rel = src.relative_to(MEASURES_ROOT)
    if len(rel.parts) < 4:
        raise HTTPException(
            status_code=400,
            detail="measure 이미지 경로는 {악보}/{페이지}/{staff}/{measure}.jpg 형식이어야 합니다.",
        )
    sheet_music = rel.parts[0]
    measure = src.stem
    return _submit_functions_crop(
        src,
        ordered,
        FUNCTIONS_PAGES_ROOT / rel.parent / measure,
        FUNCTIONS_IN_MEASURE_ROOT / rel.parent / f"{measure}.json",
        {"sheet_music": sheet_music, "measure": measure},
    )


def _submit_function_in_note(src: Path, ordered: list[Box]) -> tuple[list[str], str]:
    rel = src.relative_to(NOTES_ROOT)
    if len(rel.parts) < 5:
        raise HTTPException(
            status_code=400,
            detail="note 이미지 경로는 {악보}/{페이지}/{staff}/{measure}/{note}.jpg 형식이어야 합니다.",
        )
    sheet_music = rel.parts[0]
    note = src.stem
    return _submit_functions_crop(
        src,
        ordered,
        FUNCTIONS_PAGES_ROOT / rel.parent / note,
        FUNCTION_IN_NOTE_ROOT / rel.parent / f"{note}.json",
        {"sheet_music": sheet_music, "note": note},
    )


_SUBMIT_HANDLERS: dict[AnnotMode, Any] = {
    MODE_PAGE_STAFF: _submit_page_staff,
    MODE_STAFF_MEASURE: _submit_staff_measure,
    MODE_MEASURE_NOTE: _submit_measure_note,
    MODE_FUNCTION_IN_PAGE: _submit_function_in_page,
    MODE_FUNCTION_IN_STAFF: _submit_function_in_staff,
    MODE_FUNCTION_IN_MEASURE: _submit_function_in_measure,
    MODE_FUNCTION_IN_NOTE: _submit_function_in_note,
}


@app.get("/api/tag")
def get_tag(mode: TagMode, relative_path: str):
    src = _resolve_source(mode, relative_path)
    tag_path = _tag_json_path(mode, src)
    return {
        "ok": True,
        "mode": mode,
        "code": _read_tag_code(tag_path),
        "tag_path": tag_path.relative_to(PROJECT_ROOT).as_posix(),
    }


@app.post("/api/tag")
def save_tag(body: TagBody):
    src = _resolve_source(body.mode, body.relative_path)
    tag_path = _tag_json_path(body.mode, src)
    payload = _build_tag_payload(body.mode, src, body.code)
    written = _write_json_file(tag_path, payload)
    return {"ok": True, "mode": body.mode, "tag_path": written}


@app.post("/api/submit")
def submit(body: SubmitBody):
    if not body.boxes:
        raise HTTPException(status_code=400, detail="박스가 하나 이상 필요합니다.")

    src = _resolve_source(body.mode, body.relative_path)
    ordered = _sort_boxes_reading_order(body.boxes)

    handler = _SUBMIT_HANDLERS.get(body.mode)
    if handler is None:
        raise HTTPException(status_code=400, detail="알 수 없는 mode입니다.")

    try:
        saved, metadata = handler(src, ordered)
    except OSError as e:
        raise HTTPException(status_code=400, detail=f"이미지를 열거나 저장할 수 없습니다: {e}") from e

    return {
        "ok": True,
        "saved": saved,
        "metadata": metadata,
        "count": len(saved),
        "mode": body.mode,
    }


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

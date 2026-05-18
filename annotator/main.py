"""
로컬 이미지 박스 어노테이션 서버.
모드별로 다른 소스 디렉터리와 저장 경로를 사용합니다.

- page_staff: source/pages → source/staffs/{악보}/{페이지stem}/staff_NNN.jpg
- staff_measure: source/staffs → source/measures/{...}/{staffstem}/measure_NNN.jpg
- measure_note: source/measures → source/notes/{...}/{measurestem}/note_NNN.jpg
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

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

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}

AnnotMode = Literal["page_staff", "staff_measure", "measure_note"]

MODE_PAGE_STAFF: AnnotMode = "page_staff"
MODE_STAFF_MEASURE: AnnotMode = "staff_measure"
MODE_MEASURE_NOTE: AnnotMode = "measure_note"

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


def _source_root(mode: AnnotMode) -> Path:
    if mode == MODE_PAGE_STAFF:
        return PAGES_ROOT
    if mode == MODE_STAFF_MEASURE:
        return STAFFS_ROOT
    if mode == MODE_MEASURE_NOTE:
        return MEASURES_ROOT
    raise HTTPException(status_code=400, detail="알 수 없는 mode입니다.")


def _inside_root(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _resolve_source(mode: AnnotMode, rel: str) -> Path:
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


def _list_images_under(root: Path) -> list[str]:
    if not root.is_dir():
        return []
    out: list[str] = []
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.suffix.lower() in ALLOWED_EXT:
            out.append(p.relative_to(root).as_posix())
    return out


@app.get("/api/images")
def list_images(mode: AnnotMode = MODE_PAGE_STAFF):
    root = _source_root(mode)
    return {"images": _list_images_under(root), "mode": mode}


@app.get("/api/image/{full_path:path}")
def get_image(full_path: str, mode: AnnotMode = MODE_PAGE_STAFF):
    resolved = _resolve_source(mode, full_path)
    return FileResponse(resolved)


def _submit_page_staff(src: Path, ordered: list[Box]) -> list[str]:
    im = Image.open(src).convert("RGB")
    iw, ih = im.size
    folder_name = src.parent.name
    stem = src.stem
    dest_dir = STAFFS_ROOT / folder_name / stem
    dest_dir.mkdir(parents=True, exist_ok=True)

    saved: list[str] = []
    for idx, b in enumerate(ordered, start=1):
        x2 = min(b.x + b.w, iw)
        y2 = min(b.y + b.h, ih)
        x1 = max(0, min(b.x, iw - 1))
        y1 = max(0, min(b.y, ih - 1))
        if x2 <= x1 or y2 <= y1:
            raise HTTPException(
                status_code=400,
                detail=f"박스 {idx}가 이미지 범위 밖이거나 크기가 0입니다.",
            )

        crop = im.crop((x1, y1, x2, y2))
        out_name = f"staff_{idx:03d}.jpg"
        out_path = dest_dir / out_name
        crop.save(out_path, format="JPEG", quality=92)
        saved.append((out_path.relative_to(PROJECT_ROOT)).as_posix())

    return saved


def _submit_staff_measure(src: Path, ordered: list[Box]) -> list[str]:
    im = Image.open(src).convert("RGB")
    iw, ih = im.size
    rel = src.relative_to(STAFFS_ROOT)
    dest_dir = MEASURES_ROOT / rel.parent / src.stem
    dest_dir.mkdir(parents=True, exist_ok=True)

    saved: list[str] = []
    for idx, b in enumerate(ordered, start=1):
        x2 = min(b.x + b.w, iw)
        y2 = min(b.y + b.h, ih)
        x1 = max(0, min(b.x, iw - 1))
        y1 = max(0, min(b.y, ih - 1))
        if x2 <= x1 or y2 <= y1:
            raise HTTPException(
                status_code=400,
                detail=f"박스 {idx}가 이미지 범위 밖이거나 크기가 0입니다.",
            )

        crop = im.crop((x1, y1, x2, y2))
        out_name = f"measure_{idx:03d}.jpg"
        out_path = dest_dir / out_name
        crop.save(out_path, format="JPEG", quality=92)
        saved.append((out_path.relative_to(PROJECT_ROOT)).as_posix())

    return saved


def _submit_measure_note(src: Path, ordered: list[Box]) -> list[str]:
    im = Image.open(src).convert("RGB")
    iw, ih = im.size
    rel = src.relative_to(MEASURES_ROOT)
    dest_dir = NOTES_ROOT / rel.parent / src.stem
    dest_dir.mkdir(parents=True, exist_ok=True)

    saved: list[str] = []
    for idx, b in enumerate(ordered, start=1):
        x2 = min(b.x + b.w, iw)
        y2 = min(b.y + b.h, ih)
        x1 = max(0, min(b.x, iw - 1))
        y1 = max(0, min(b.y, ih - 1))
        if x2 <= x1 or y2 <= y1:
            raise HTTPException(
                status_code=400,
                detail=f"박스 {idx}가 이미지 범위 밖이거나 크기가 0입니다.",
            )

        crop = im.crop((x1, y1, x2, y2))
        out_name = f"note_{idx:03d}.jpg"
        out_path = dest_dir / out_name
        crop.save(out_path, format="JPEG", quality=92)
        saved.append((out_path.relative_to(PROJECT_ROOT)).as_posix())

    return saved


@app.post("/api/submit")
def submit(body: SubmitBody):
    if not body.boxes:
        raise HTTPException(status_code=400, detail="박스가 하나 이상 필요합니다.")

    src = _resolve_source(body.mode, body.relative_path)
    ordered = _sort_boxes_reading_order(body.boxes)

    try:
        if body.mode == MODE_PAGE_STAFF:
            saved = _submit_page_staff(src, ordered)
        elif body.mode == MODE_STAFF_MEASURE:
            saved = _submit_staff_measure(src, ordered)
        else:
            saved = _submit_measure_note(src, ordered)
    except OSError as e:
        raise HTTPException(status_code=400, detail=f"이미지를 열거나 저장할 수 없습니다: {e}") from e

    return {"ok": True, "saved": saved, "count": len(saved), "mode": body.mode}


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

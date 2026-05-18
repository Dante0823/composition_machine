"""
로컬 이미지 박스 어노테이션 서버.
프로젝트 루트의 source/pages 이미지를 불러오고,
제출 시 source/staffs/{페이지폴더}/{페이지파일stem}/staff_NNN.jpg 형태로 저장합니다.
"""

from __future__ import annotations

from pathlib import Path

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

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}

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
    """relative_path: source/pages 기준, 예: sheet_music_01/page_001.jpg"""

    relative_path: str
    boxes: list[Box]


def _inside_pages(path: Path) -> bool:
    try:
        path.resolve().relative_to(PAGES_ROOT.resolve())
    except ValueError:
        return False
    return True


def _resolve_page(rel: str) -> Path:
    rel_norm = rel.replace("\\", "/").lstrip("/")
    candidate = (PAGES_ROOT / rel_norm).resolve()
    if not _inside_pages(candidate):
        raise HTTPException(status_code=400, detail="경로가 허용 범위를 벗어났습니다.")
    if not candidate.is_file():
        raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다.")
    if candidate.suffix.lower() not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail="지원하지 않는 이미지 형식입니다.")
    return candidate


def _sort_boxes_reading_order(boxes: list[Box]) -> list[Box]:
    """위에서 아래, 같은 줄에서는 왼쪽에서 오른쪽 (좌상단 기준)."""

    return sorted(boxes, key=lambda b: (b.y, b.x))


@app.get("/api/images")
def list_images():
    if not PAGES_ROOT.is_dir():
        return {"images": []}

    out: list[str] = []
    for p in sorted(PAGES_ROOT.rglob("*")):
        if p.is_file() and p.suffix.lower() in ALLOWED_EXT:
            rel = p.relative_to(PAGES_ROOT).as_posix()
            out.append(rel)
    return {"images": out}


@app.get("/api/image/{full_path:path}")
def get_image(full_path: str):
    resolved = _resolve_page(full_path)
    return FileResponse(resolved)


@app.post("/api/submit")
def submit(body: SubmitBody):
    if not body.boxes:
        raise HTTPException(status_code=400, detail="박스가 하나 이상 필요합니다.")

    src = _resolve_page(body.relative_path)
    ordered = _sort_boxes_reading_order(body.boxes)

    try:
        im = Image.open(src).convert("RGB")
    except OSError as e:
        raise HTTPException(status_code=400, detail=f"이미지를 열 수 없습니다: {e}") from e

    iw, ih = im.size
    folder_name = src.parent.name
    stem = src.stem
    suffix = ".jpg"

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
        # 예: source/staffs/sheet_music_01/page_001/staff_001.jpg (순서는 좌상단 정렬 후)
        out_name = f"staff_{idx:03d}{suffix}"
        out_path = dest_dir / out_name
        crop.save(out_path, format="JPEG", quality=92)
        saved.append((dest_dir.relative_to(PROJECT_ROOT) / out_name).as_posix())

    return {"ok": True, "saved": saved, "count": len(saved)}


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

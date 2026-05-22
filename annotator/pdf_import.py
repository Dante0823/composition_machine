"""PDF 업로드 → works/{work_id}/assets + images/pages 변환."""

from __future__ import annotations

import json
import re
from pathlib import Path

import fitz

try:
    from .storage_layout import (
        PROJECT_ROOT,
        catalog_path,
        default_pdf_path,
        empty_catalog,
        images_dir,
        read_catalog,
        work_dir,
    )
except ImportError:
    from storage_layout import (
        PROJECT_ROOT,
        catalog_path,
        default_pdf_path,
        empty_catalog,
        images_dir,
        read_catalog,
        work_dir,
    )

WORK_ID_RE = re.compile(r"^[a-zA-Z0-9_-]+$")
DEFAULT_DPI = 200


def validate_work_id(work: str) -> str:
    work = work.strip()
    if not work or not WORK_ID_RE.match(work) or work.startswith("_"):
        raise ValueError("work_id는 영문, 숫자, _, - 만 사용할 수 있습니다.")
    return work


def import_work_pdf(work: str, pdf_bytes: bytes, dpi: int = DEFAULT_DPI) -> dict:
    work = validate_work_id(work)
    if not pdf_bytes:
        raise ValueError("PDF 파일이 비어 있습니다.")

    assets_dir = work_dir(work) / "assets"
    pages_dir = images_dir(work, "pages")
    assets_dir.mkdir(parents=True, exist_ok=True)
    pages_dir.mkdir(parents=True, exist_ok=True)

    pdf_path = default_pdf_path(work)
    pdf_path.write_bytes(pdf_bytes)

    for old_page in pages_dir.glob("page_*.jpg"):
        old_page.unlink()

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)
    saved_pages: list[str] = []

    try:
        for page_index in range(len(doc)):
            page = doc.load_page(page_index)
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            out_path = pages_dir / f"page_{page_index + 1:03d}.jpg"
            pix.save(str(out_path), output="jpeg", jpg_quality=92)
            saved_pages.append(out_path.relative_to(PROJECT_ROOT).as_posix())
    finally:
        doc.close()

    catalog = read_catalog(work) if catalog_path(work).is_file() else empty_catalog(work)
    catalog["work"] = work
    catalog["pdf"] = pdf_path.relative_to(PROJECT_ROOT).as_posix()

    with catalog_path(work).open("w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=4, ensure_ascii=False)
        f.write("\n")

    return {
        "work": work,
        "page_count": len(saved_pages),
        "pdf_path": catalog["pdf"],
        "pages": saved_pages,
        "catalog_path": catalog_path(work).relative_to(PROJECT_ROOT).as_posix(),
    }

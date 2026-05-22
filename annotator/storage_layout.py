"""
works/{work_id}/ 아래로 이미지·메타데이터를 통합하는 저장 레이아웃.

works/sheet_music_01/
  catalog.json
  images/
    pages/page_001.jpg
    staffs/page_001/staff_001.jpg
    measures/page_001/staff_001/measure_001.jpg
    notes/page_001/staff_001/measure_001/note_001.jpg
    functions/page_001/.../function_001.jpg
  meta/
    crop/staffs/pages/page_001.json          # page_staff 결과
    crop/measures/staffs/page_001/staff_001.json
    crop/notes/measures/.../measure_001.json
    crop/functions/pages/page_001.json     # function_in_page 결과
    tag/code/pages/page_001.json
    tag/code/staffs/page_001/staff_001.json
    tag/function/functions/page_001/.../function_001.json
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WORKS_ROOT = PROJECT_ROOT / "works"
SCHEMA_ROOT = WORKS_ROOT / "_schema"

ImageLayer = Literal["pages", "staffs", "measures", "notes", "functions"]
CropOutputLayer = Literal["staffs", "measures", "notes", "functions"]

AnnotMode = Literal[
    "page_staff",
    "staff_measure",
    "measure_note",
    "function_in_page",
    "function_in_staff",
    "function_in_measure",
    "function_in_note",
]

TagMode = Literal[
    "code_of_page",
    "code_of_staff",
    "code_of_measure",
    "code_of_note",
    "tag_of_page_function",
    "tag_of_staff_function",
    "tag_of_measure_function",
    "tag_of_note_function",
    "meta_of_work",
]

CatalogMode = Literal["meta_of_work"]

AppMode = AnnotMode | TagMode

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}

FUNCTION_TAG_MODES: frozenset[str] = frozenset(
    {
        "tag_of_page_function",
        "tag_of_staff_function",
        "tag_of_measure_function",
        "tag_of_note_function",
    }
)

# functions/ 아래 상대 경로 segment 수 (work_id 제외)
FUNCTION_TAG_DEPTH: dict[str, int] = {
    "tag_of_page_function": 2,
    "tag_of_staff_function": 3,
    "tag_of_measure_function": 4,
    "tag_of_note_function": 5,
}

MODE_SOURCE_LAYER: dict[str, ImageLayer] = {
    "page_staff": "pages",
    "staff_measure": "staffs",
    "measure_note": "measures",
    "function_in_page": "pages",
    "function_in_staff": "staffs",
    "function_in_measure": "measures",
    "function_in_note": "notes",
    "code_of_page": "pages",
    "code_of_staff": "staffs",
    "code_of_measure": "measures",
    "code_of_note": "notes",
    "tag_of_page_function": "functions",
    "tag_of_staff_function": "functions",
    "tag_of_measure_function": "functions",
    "tag_of_note_function": "functions",
}

MODE_CROP_OUTPUT: dict[str, CropOutputLayer] = {
    "page_staff": "staffs",
    "staff_measure": "measures",
    "measure_note": "notes",
    "function_in_page": "functions",
    "function_in_staff": "functions",
    "function_in_measure": "functions",
    "function_in_note": "functions",
}

MODE_CHILD_LAYER: dict[str, ImageLayer] = {
    "page_staff": "staffs",
    "staff_measure": "measures",
    "measure_note": "notes",
    "function_in_page": "functions",
    "function_in_staff": "functions",
    "function_in_measure": "functions",
    "function_in_note": "functions",
}

MODE_SOURCE_LABEL: dict[str, str] = {
    "page_staff": "works/{id}/images/pages",
    "staff_measure": "works/{id}/images/staffs",
    "measure_note": "works/{id}/images/measures",
    "function_in_page": "works/{id}/images/pages",
    "function_in_staff": "works/{id}/images/staffs",
    "function_in_measure": "works/{id}/images/measures",
    "function_in_note": "works/{id}/images/notes",
    "code_of_page": "works/{id}/images/pages",
    "code_of_staff": "works/{id}/images/staffs",
    "code_of_measure": "works/{id}/images/measures",
    "code_of_note": "works/{id}/images/notes",
    "tag_of_page_function": "works/{id}/images/functions",
    "tag_of_staff_function": "works/{id}/images/functions",
    "tag_of_measure_function": "works/{id}/images/functions",
    "tag_of_note_function": "works/{id}/images/functions",
    "meta_of_work": "works/{id}/assets + catalog.json",
}

CATALOG_MODE = "meta_of_work"


def is_function_tag_mode(mode: AppMode) -> bool:
    return mode in FUNCTION_TAG_MODES


def source_layer(mode: AppMode) -> ImageLayer:
    layer = MODE_SOURCE_LAYER.get(mode)
    if layer is None:
        raise ValueError(f"알 수 없는 mode: {mode}")
    return layer


def parse_relative_path(rel: str) -> tuple[str, tuple[str, ...]]:
    rel_norm = rel.replace("\\", "/").lstrip("/")
    parts = tuple(p for p in rel_norm.split("/") if p)
    if len(parts) < 2:
        raise ValueError("relative_path는 {work_id}/... 형식이어야 합니다.")
    return parts[0], parts[1:]


def images_dir(work: str, layer: ImageLayer) -> Path:
    return WORKS_ROOT / work / "images" / layer


def resolve_image(mode: AppMode, rel: str) -> Path:
    work, rest = parse_relative_path(rel)
    candidate = (images_dir(work, source_layer(mode)).joinpath(*rest)).resolve()
    root = images_dir(work, source_layer(mode)).resolve()
    if not _inside_root(candidate, root):
        raise ValueError("경로가 허용 범위를 벗어났습니다.")
    return candidate


def image_relative_path(work: str, layer: ImageLayer, path_under_layer: Path | str) -> str:
    under = Path(path_under_layer).as_posix().lstrip("/")
    return f"{work}/{under}"


def source_descriptor(work: str, layer: ImageLayer, path_under_layer: Path) -> dict[str, str]:
    rel = path_under_layer.as_posix()
    return {"layer": layer, "path": f"{layer}/{rel}"}


def list_work_ids() -> list[str]:
    if not WORKS_ROOT.is_dir():
        return []
    return sorted(
        p.name
        for p in WORKS_ROOT.iterdir()
        if p.is_dir() and not p.name.startswith("_")
    )


def list_images(mode: AppMode) -> list[str]:
    layer = source_layer(mode)
    out: list[str] = []
    for work in list_work_ids():
        base = images_dir(work, layer)
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in ALLOWED_EXT:
                continue
            if is_function_tag_mode(mode):
                rel = path.relative_to(base)
                if len(rel.parts) != FUNCTION_TAG_DEPTH[mode]:
                    continue
            rel = path.relative_to(base).as_posix()
            out.append(f"{work}/{rel}")
    return out


def crop_output_dir(work: str, output_layer: CropOutputLayer, parent_under_layer: Path) -> Path:
    return images_dir(work, output_layer) / parent_under_layer


def crop_meta_path(work: str, output_layer: CropOutputLayer, source_layer_name: ImageLayer, source_under: Path) -> Path:
    return (
        WORKS_ROOT
        / work
        / "meta"
        / "crop"
        / output_layer
        / source_layer_name
        / source_under.with_suffix(".json")
    )


def code_tag_path(work: str, source_layer_name: ImageLayer, source_under: Path) -> Path:
    return (
        WORKS_ROOT
        / work
        / "meta"
        / "tag"
        / "code"
        / source_layer_name
        / source_under.with_suffix(".json")
    )


def function_tag_path(work: str, function_under: Path) -> Path:
    return (
        WORKS_ROOT
        / work
        / "meta"
        / "tag"
        / "function"
        / "functions"
        / function_under.with_suffix(".json")
    )


def build_crop_payload(
    work: str,
    source_layer_name: ImageLayer,
    source_under: Path,
    child_layer: ImageLayer,
    items: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "version": 1,
        "work": work,
        "source": source_descriptor(work, source_layer_name, source_under),
        "items": items,
        "item_layer": child_layer,
    }


def build_code_tag_payload(work: str, source_layer_name: ImageLayer, source_under: Path, code: str) -> dict[str, Any]:
    return {
        "version": 1,
        "work": work,
        "source": source_descriptor(work, source_layer_name, source_under),
        "code": code,
    }


def build_function_tag_payload(work: str, function_under: Path, tag: str) -> dict[str, Any]:
    return {
        "version": 1,
        "work": work,
        "source": source_descriptor(work, "functions", function_under),
        "tag": tag,
    }


def is_catalog_mode(mode: AppMode) -> bool:
    return mode == CATALOG_MODE


def work_dir(work: str) -> Path:
    return WORKS_ROOT / work


def catalog_path(work: str) -> Path:
    return work_dir(work) / "catalog.json"


def default_pdf_path(work: str) -> Path:
    return work_dir(work) / "assets" / f"{work}.pdf"


def resolve_work_pdf(work: str) -> Path:
    catalog = catalog_path(work)
    if catalog.is_file():
        try:
            with catalog.open(encoding="utf-8") as f:
                data = json.load(f)
            pdf_field = data.get("pdf") if isinstance(data, dict) else None
            if isinstance(pdf_field, str) and pdf_field.strip():
                candidate = (PROJECT_ROOT / pdf_field.replace("\\", "/")).resolve()
                if candidate.is_file():
                    return candidate
        except (OSError, json.JSONDecodeError):
            pass
    default = default_pdf_path(work)
    if default.is_file():
        return default
    raise FileNotFoundError(f"PDF를 찾을 수 없습니다: {work}")


def list_catalog_works() -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for work in list_work_ids():
        if work in seen:
            continue
        has_pdf = False
        try:
            resolve_work_pdf(work)
            has_pdf = True
        except FileNotFoundError:
            has_pdf = default_pdf_path(work).is_file()
        has_pages = images_dir(work, "pages").is_dir() and any(images_dir(work, "pages").glob("page_*.jpg"))
        if has_pdf or has_pages or catalog_path(work).is_file():
            out.append(work)
            seen.add(work)
    return out


def empty_catalog(work: str) -> dict[str, Any]:
    pdf_rel = f"works/{work}/assets/{work}.pdf"
    return {
        "version": 1,
        "work": work,
        "pdf": pdf_rel,
        "music_info": {
            "title_info": {
                "title": "",
                "subtitle": "",
                "display_title": "",
            },
            "composer_info": {
                "composer": "",
                "display_composer": "",
            },
        },
        "copyright_info": {
            "copyright_free": None,
        },
        "analysis_info": {
            "content": "",
        },
    }


def normalize_catalog(data: dict[str, Any], work: str) -> dict[str, Any]:
    base = empty_catalog(work)
    mi = data.get("music_info") if isinstance(data.get("music_info"), dict) else {}
    ti = mi.get("title_info") if isinstance(mi.get("title_info"), dict) else {}
    ci = mi.get("composer_info") if isinstance(mi.get("composer_info"), dict) else {}
    cr = data.get("copyright_info") if isinstance(data.get("copyright_info"), dict) else {}
    ai = data.get("analysis_info") if isinstance(data.get("analysis_info"), dict) else {}

    copyright_free = cr.get("copyright_free")
    if copyright_free is None and "is_copyright" in cr:
        legacy = cr.get("is_copyright")
        if isinstance(legacy, bool):
            copyright_free = not legacy

    base["pdf"] = data.get("pdf") or base["pdf"]
    base["music_info"]["title_info"] = {
        "title": str(ti.get("title") or ""),
        "subtitle": str(ti.get("subtitle") or ""),
        "display_title": str(ti.get("display_title") or ""),
    }
    base["music_info"]["composer_info"] = {
        "composer": str(ci.get("composer") or ""),
        "display_composer": str(ci.get("display_composer") or ""),
    }
    base["copyright_info"]["copyright_free"] = copyright_free if isinstance(copyright_free, bool) else None
    base["analysis_info"]["content"] = str(ai.get("content") or "")
    return base


def catalog_is_complete(data: dict[str, Any]) -> bool:
    normalized = normalize_catalog(data, str(data.get("work") or ""))
    ti = normalized["music_info"]["title_info"]
    ci = normalized["music_info"]["composer_info"]
    strings = [
        ti["title"],
        ti["subtitle"],
        ti["display_title"],
        ci["composer"],
        ci["display_composer"],
        normalized["analysis_info"]["content"],
    ]
    if not all(isinstance(s, str) and s.strip() for s in strings):
        return False
    return isinstance(normalized["copyright_info"]["copyright_free"], bool)


def read_catalog(work: str) -> dict[str, Any]:
    path = catalog_path(work)
    if not path.is_file():
        return empty_catalog(work)
    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return empty_catalog(work)
    if not isinstance(data, dict):
        return empty_catalog(work)
    return normalize_catalog(data, work)


def build_catalog_payload(body: dict[str, Any], work: str) -> dict[str, Any]:
    current = read_catalog(work)

    current["music_info"]["title_info"]["title"] = str(body.get("title") or "").strip()
    current["music_info"]["title_info"]["subtitle"] = str(body.get("subtitle") or "").strip()
    current["music_info"]["title_info"]["display_title"] = str(body.get("display_title") or "").strip()
    current["music_info"]["composer_info"]["composer"] = str(body.get("composer") or "").strip()
    current["music_info"]["composer_info"]["display_composer"] = str(body.get("display_composer") or "").strip()
    current["analysis_info"]["content"] = str(body.get("analysis") or "").strip()

    cf = body.get("copyright_free")
    if cf is True or cf is False:
        current["copyright_info"]["copyright_free"] = cf
    elif isinstance(cf, str):
        if cf == "true":
            current["copyright_info"]["copyright_free"] = True
        elif cf == "false":
            current["copyright_info"]["copyright_free"] = False

    try:
        pdf = resolve_work_pdf(work)
        current["pdf"] = pdf.relative_to(PROJECT_ROOT).as_posix()
    except FileNotFoundError:
        current["pdf"] = f"works/{work}/assets/{work}.pdf"

    return current


def _inside_root(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True

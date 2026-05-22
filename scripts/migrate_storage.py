#!/usr/bin/env python3
"""기존 source/ + data/ 구조를 works/{work_id}/ 통합 레이아웃으로 마이그레이션."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WORKS_ROOT = PROJECT_ROOT / "works"

OLD_SOURCE = PROJECT_ROOT / "source"
OLD_POSITION = PROJECT_ROOT / "data" / "position_data"
OLD_TAG_PAGES = PROJECT_ROOT / "data" / "tag_data" / "pages"
OLD_TAG_FUNCTIONS = PROJECT_ROOT / "data" / "tag_data" / "functions" / "pages"
OLD_CATALOG = PROJECT_ROOT / "data" / "data.json"

IMAGE_MOVES = (
    ("pages", OLD_SOURCE / "pages"),
    ("staffs", OLD_SOURCE / "staffs"),
    ("measures", OLD_SOURCE / "measures"),
    ("notes", OLD_SOURCE / "notes"),
    ("functions", OLD_SOURCE / "functions" / "pages"),
)

CROP_ITEM_LAYER = {
    "staffs_in_page": "staffs",
    "measures_in_staff": "measures",
    "notes_in_measure": "notes",
    "functions_in_page": "functions",
    "functions_in_staff": "functions",
    "functions_in_measure": "functions",
    "function_in_note": "functions",
}

CROP_ARRAY_KEYS = ("staffs", "measures", "notes", "functions", "items")


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else None


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        f.write("\n")


def extract_items(data: dict[str, Any]) -> list[dict[str, Any]]:
    for key in CROP_ARRAY_KEYS:
        value = data.get(key)
        if isinstance(value, list):
            return value
    return []


def convert_crop_payload(
    data: dict[str, Any],
    work: str,
    source_layer: str,
    source_rel: Path,
    item_layer: str,
) -> dict[str, Any]:
    return {
        "version": 1,
        "work": work,
        "source": {"layer": source_layer, "path": f"{source_layer}/{source_rel.as_posix()}"},
        "item_layer": item_layer,
        "items": extract_items(data),
    }


def migrate_images() -> int:
    moved = 0
    for layer, old_root in IMAGE_MOVES:
        if not old_root.is_dir():
            continue
        for path in old_root.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(old_root)
            if len(rel.parts) < 1:
                continue
            work = rel.parts[0]
            rest = Path(*rel.parts[1:])
            dest = WORKS_ROOT / work / "images" / layer / rest
            if dest.exists():
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)
            moved += 1
    return moved


def migrate_crop_staffs_in_page() -> int:
    root = OLD_POSITION / "staffs_in_page"
    count = 0
    for path in root.rglob("*.json"):
        if path.name.endswith(".template"):
            continue
        rel = path.relative_to(root)
        work, page_json = rel.parts[0], rel.parts[1]
        page = Path(page_json).stem
        payload = convert_crop_payload(
            load_json(path) or {},
            work,
            "pages",
            Path(f"{page}.jpg"),
            "staffs",
        )
        write_json(WORKS_ROOT / work / "meta" / "crop" / "staffs" / "pages" / f"{page}.json", payload)
        count += 1
    return count


def migrate_crop_measures_in_staff() -> int:
    root = OLD_POSITION / "measures_in_staff"
    count = 0
    for path in root.rglob("*.json"):
        if path.name.endswith(".template"):
            continue
        rel = path.relative_to(root)
        work, page, staff_json = rel.parts[0], rel.parts[1], rel.parts[2]
        staff = Path(staff_json).stem
        payload = convert_crop_payload(
            load_json(path) or {},
            work,
            "staffs",
            Path(page) / f"{staff}.jpg",
            "measures",
        )
        write_json(
            WORKS_ROOT / work / "meta" / "crop" / "measures" / "staffs" / page / f"{staff}.json",
            payload,
        )
        count += 1
    return count


def migrate_crop_notes_in_measure() -> int:
    root = OLD_POSITION / "notes_in_measure"
    count = 0
    for path in root.rglob("*.json"):
        if path.name.endswith(".template"):
            continue
        rel = path.relative_to(root)
        work, page, staff, measure_json = rel.parts[0], rel.parts[1], rel.parts[2], rel.parts[3]
        measure = Path(measure_json).stem
        payload = convert_crop_payload(
            load_json(path) or {},
            work,
            "measures",
            Path(page) / staff / f"{measure}.jpg",
            "notes",
        )
        write_json(
            WORKS_ROOT
            / work
            / "meta"
            / "crop"
            / "notes"
            / "measures"
            / page
            / staff
            / f"{measure}.json",
            payload,
        )
        count += 1
    return count


def migrate_crop_functions(kind: str, source_layer: str, source_parts: int) -> int:
    root = OLD_POSITION / kind
    count = 0
    for path in root.rglob("*.json"):
        if path.name.endswith(".template"):
            continue
        rel = path.relative_to(root)
        work = rel.parts[0]
        tail = rel.parts[1:]
        stem = Path(tail[-1]).stem
        if source_parts == 1:
            source_rel = Path(f"{stem}.jpg")
        elif source_parts == 2:
            source_rel = Path(tail[0]) / f"{stem}.jpg"
        elif source_parts == 3:
            source_rel = Path(tail[0]) / tail[1] / f"{stem}.jpg"
        else:
            source_rel = Path(tail[0]) / tail[1] / tail[2] / f"{stem}.jpg"

        payload = convert_crop_payload(
            load_json(path) or {},
            work,
            source_layer,
            source_rel,
            "functions",
        )
        dest = WORKS_ROOT / work / "meta" / "crop" / "functions" / source_layer / source_rel.with_suffix(".json")
        write_json(dest, payload)
        count += 1
    return count


def migrate_code_tags() -> int:
    count = 0
    if not OLD_TAG_PAGES.is_dir():
        return 0
    for path in OLD_TAG_PAGES.rglob("*.json"):
        if path.name.endswith(".template"):
            continue
        rel = path.relative_to(OLD_TAG_PAGES)
        work = rel.parts[0]
        tail = rel.parts[1:]
        if len(tail) == 1:
            layer, source_rel = "pages", Path(tail[0])
        elif len(tail) == 2:
            layer, source_rel = "staffs", Path(tail[0]) / tail[1]
        elif len(tail) == 3:
            layer, source_rel = "measures", Path(tail[0]) / tail[1] / tail[2]
        elif len(tail) == 4:
            layer, source_rel = "notes", Path(tail[0]) / tail[1] / tail[2] / tail[3]
        else:
            continue

        old = load_json(path) or {}
        payload = {
            "version": 1,
            "work": work,
            "source": {"layer": layer, "path": f"{layer}/{source_rel.as_posix()}"},
            "code": old.get("code", ""),
        }
        write_json(
            WORKS_ROOT / work / "meta" / "tag" / "code" / layer / source_rel.with_suffix(".json"),
            payload,
        )
        count += 1
    return count


def migrate_function_tags() -> int:
    count = 0
    if not OLD_TAG_FUNCTIONS.is_dir():
        return 0
    for path in OLD_TAG_FUNCTIONS.rglob("*.json"):
        if path.name.endswith(".template"):
            continue
        rel = path.relative_to(OLD_TAG_FUNCTIONS)
        work = rel.parts[0]
        fn_rel = Path(*rel.parts[1:])
        old = load_json(path) or {}
        payload = {
            "version": 1,
            "work": work,
            "source": {"layer": "functions", "path": f"functions/{fn_rel.as_posix()}"},
            "tag": old.get("tag", ""),
        }
        write_json(
            WORKS_ROOT / work / "meta" / "tag" / "function" / "functions" / fn_rel,
            payload,
        )
        count += 1
    return count


def migrate_catalog() -> int:
    data = load_json(OLD_CATALOG)
    if not data:
        return 0
    work = data.get("file_name") or data.get("work")
    if not isinstance(work, str) or not work:
        return 0
    payload = {
        "version": 1,
        "work": work,
        "pdf": f"works/{work}/assets/{work}.pdf",
        "music_info": data.get("music_info", {}),
        "copyright_info": data.get("copyright_info", {}),
    }
    write_json(WORKS_ROOT / work / "catalog.json", payload)
    old_pdf = PROJECT_ROOT / "source" / "pdfs" / f"{work}.pdf"
    if old_pdf.is_file():
        dest = WORKS_ROOT / work / "assets" / f"{work}.pdf"
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            shutil.copy2(old_pdf, dest)
    return 1


def main() -> None:
    WORKS_ROOT.mkdir(parents=True, exist_ok=True)
    stats = {
        "images": migrate_images(),
        "crop_staffs": migrate_crop_staffs_in_page(),
        "crop_measures": migrate_crop_measures_in_staff(),
        "crop_notes": migrate_crop_notes_in_measure(),
        "crop_fn_page": migrate_crop_functions("functions_in_page", "pages", 1),
        "crop_fn_staff": migrate_crop_functions("functions_in_staff", "staffs", 2),
        "crop_fn_measure": migrate_crop_functions("functions_in_measure", "measures", 3),
        "crop_fn_note": migrate_crop_functions("function_in_note", "notes", 4),
        "tag_code": migrate_code_tags(),
        "tag_function": migrate_function_tags(),
        "catalog": migrate_catalog(),
    }
    print("Migration complete:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()

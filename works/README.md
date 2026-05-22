# works/ 저장 레이아웃

악보 하나 = `works/{work_id}/` 폴더 하나.

## 디렉터리

```
works/sheet_music_01/
  catalog.json              # 악보 메타 (제목, 작곡가, PDF 경로)
  assets/                   # PDF 등 원본 자산
  images/                   # 크롭·작업 대상 래스터 이미지
    pages/page_001.jpg
    staffs/page_001/staff_001.jpg
    measures/page_001/staff_001/measure_001.jpg
    notes/page_001/staff_001/measure_001/note_001.jpg
    functions/page_001/.../function_001.jpg
  meta/
    crop/                   # 크롭 결과 메타 (위치 정보)
      staffs/pages/page_001.json
      measures/staffs/page_001/staff_001.json
      notes/measures/.../measure_001.json
      functions/pages/page_001.json
    tag/
      code/                 # Strudel 코드
        pages/page_001.json
        staffs/page_001/staff_001.json
      function/             # function 이미지 태그
        functions/page_001/.../function_001.json
```

## JSON 공통 규칙

- `version`: 스키마 버전 (현재 `1`)
- `work`: 악보 ID (`sheet_music_01`)
- `source`: `{ "layer", "path" }` — 메타가 참조하는 **원본 이미지**
- 크롭: `item_layer` + `items[]` (`index`, `name`, `position`)
- 코드 태그: `code` 필드
- 함수 태그: `tag` 필드

스키마 예시: `_schema/*.example.json`

## API relative_path

모드별 이미지 목록·선택 경로는 `{work_id}/...` 형식 (예: `sheet_music_01/page_001/staff_001.jpg`).

## 마이그레이션

기존 `source/` + `data/` 구조에서 이 레이아웃으로 옮길 때:

```bash
python scripts/migrate_storage.py
```

기존 폴더는 백업용으로 남겨 두었습니다. 새 작업은 `works/`만 사용합니다.

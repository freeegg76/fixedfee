# Skill: sheets-writer

Template 탭 복제와 셀 값 일괄 입력 두 가지 작업을 담당하는 스킬.

## 스크립트

- `copy_template_tab.py`: Template 탭 복제 + 탭 이름 변경
- `batch_write_cells.py`: 플레이스홀더 교체를 위한 셀 값 일괄 입력

---

## 1. copy_template_tab.py

### 사용 시점

STEP 3-3: 마스터 스프레드시트의 Template 탭을 고객사 Sheets에 복사하고 `YYYY.MM`으로 이름 변경.

### 호출 방법

```bash
python .claude/skills/sheets-writer/scripts/copy_template_tab.py \
  --master-sheet-id <MASTER_ID> \
  --target-sheet-id <CLIENT_SHEET_KEY> \
  --tab-name "2025.03" \
  --template-sheet-id <TEMPLATE_SHEET_ID>
```

- `--master-sheet-id`: 마스터 스프레드시트 ID (`MASTER_SHEET_ID` 환경변수 값)
- `--target-sheet-id`: Fixed 탭 `Key` 컬럼의 고객사 Sheets 파일 ID
- `--tab-name`: 귀속월을 `YYYY.MM` 형식으로 변환한 값 (예: `2025/03` → `2025.03`)
- `--template-sheet-id`: `sheets-reader`의 `--get-sheet-id` 로 조회한 Template sheetId (정수)

### 출력 형식

```json
{"new_sheet_id": 987654, "sheet_url": "https://docs.google.com/spreadsheets/d/.../edit#gid=987654"}
```

---

## 2. batch_write_cells.py

### 사용 시점

STEP 3-5: `variable-mapper`가 찾은 플레이스홀더 위치에 실제 값을 입력.

### 호출 방법

```bash
python .claude/skills/sheets-writer/scripts/batch_write_cells.py \
  --spreadsheet-id <CLIENT_SHEET_KEY> \
  --tab-name "2025.03" \
  --cells '{"B3": "삼성전자", "C5": "1000000", "D7": "2025/03"}'
```

- `--cells`: `{셀주소: 값}` 형식의 JSON 문자열
  - 셀주소는 `variable-mapper`의 `find_placeholders` 출력값 사용

### 출력 형식

```json
{"updated_cells": 5}
```

---

## 환경변수

- `GOOGLE_SERVICE_ACCOUNT_KEY`: Service Account JSON 키파일 경로 (필수)

## 재시도 정책

- 실패 시 MAX_RETRY(기본 1)회 재시도
- 재시도 후에도 실패하면 해당 고객사 스킵 + 로그 기록

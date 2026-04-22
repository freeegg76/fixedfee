# Skill: sheets-reader

Google Sheets 탭의 데이터를 읽거나 탭 목록을 조회하는 스킬.

## 스크립트

`.claude/skills/sheets-reader/scripts/read_sheets.py`

## 사용 시점

| 상황 | 사용 모드 |
|------|----------|
| 마스터 스프레드시트의 Client, Fixed, Instruction 탭 읽기 (STEP 1) | `--tab 탭명` |
| Template 탭의 sheetId 조회 (STEP 1, copyTo 전 필요) | `--get-sheet-id --tab Template` |
| 고객사 Sheets 탭 목록 확인 (STEP 3-2 중복 확인) | `--list-tabs` |
| 복제된 탭의 전체 셀 값 읽기 (STEP 3-5 플레이스홀더 스캔 전) | `--tab 탭명` |

## 호출 방법

```bash
# 탭 데이터 읽기
python .claude/skills/sheets-reader/scripts/read_sheets.py \
  --spreadsheet-id <SHEET_ID> \
  --tab "Client"

# 탭 목록 조회
python .claude/skills/sheets-reader/scripts/read_sheets.py \
  --spreadsheet-id <SHEET_ID> \
  --list-tabs

# 특정 탭의 sheetId 조회
python .claude/skills/sheets-reader/scripts/read_sheets.py \
  --spreadsheet-id <SHEET_ID> \
  --get-sheet-id \
  --tab "Template"
```

## 출력 형식

```jsonc
// --tab 모드
{"tab": "Client", "rows": [["헤더1","헤더2",...], ["값1","값2",...], ...]}

// --list-tabs 모드
{"tabs": [{"title": "Client", "sheetId": 0}, {"title": "2025.03", "sheetId": 123456}]}

// --get-sheet-id 모드
{"sheet_id": 123456}
```

## 환경변수

- `GOOGLE_SERVICE_ACCOUNT_KEY`: Service Account JSON 키파일 경로 (필수)

## 오류 처리

- `GOOGLE_SERVICE_ACCOUNT_KEY` 미설정 시 `{"error": "..."}` 출력 후 exit 1
- 탭 미존재 시 `{"error": "탭을 찾을 수 없음: 탭명"}` 출력 후 exit 1

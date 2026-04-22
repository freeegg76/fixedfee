# Google Sheets API 참고 메모

## 인증 설정

### Service Account 생성 절차

1. Google Cloud Console → IAM & Admin → Service Accounts
2. 새 Service Account 생성
3. JSON 키 다운로드
4. 마스터 스프레드시트 및 모든 고객사 Sheets에서 해당 Service Account 이메일을 편집자로 추가

### 환경변수 설정

```bash
export GOOGLE_SERVICE_ACCOUNT_KEY="/path/to/service-account-key.json"
export MASTER_SHEET_ID="1EVyVqFvntsWBYbeEO6Uxv2X6JbDBxP-er97WFd0U5SM"
export MAX_RETRY=1
```

conda 환경을 사용하는 경우 `conda activate <환경명>` 후 위 변수를 설정하거나,
`.env` 파일에 저장 후 `source .env`로 로드한다.

### 필수 패키지 설치

```bash
pip install google-auth google-auth-httplib2 google-api-python-client
```

---

## API 사용 레퍼런스

### 탭 데이터 읽기

```python
service.spreadsheets().values().get(
    spreadsheetId=spreadsheet_id,
    range="Client"          # 탭명만 지정하면 전체 범위
).execute()
# 반환: {"values": [["헤더1","헤더2",...], ["값1","값2",...], ...]}
```

### 탭 목록 및 sheetId 조회

```python
service.spreadsheets().get(
    spreadsheetId=spreadsheet_id,
    fields="sheets.properties"
).execute()
# 반환: {"sheets": [{"properties": {"sheetId": 0, "title": "Client"}}, ...]}
```

### Template 탭 복제 (copyTo)

```python
# 마스터 → 고객사 Sheets로 복사
service.spreadsheets().sheets().copyTo(
    spreadsheetId=master_sheet_id,          # 원본 스프레드시트
    sheetId=template_sheet_id,              # Template 탭 sheetId (정수)
    body={"destinationSpreadsheetId": target_sheet_id}
).execute()
# 반환: {"sheetId": 새sheetId, "title": "Template의 복사본", ...}
```

> **주의**: copyTo 결과 탭 이름이 "Template의 복사본"으로 생성됨.
> 반드시 후속으로 UpdateSheetPropertiesRequest로 이름을 변경해야 함.

### 탭 이름 변경

```python
service.spreadsheets().batchUpdate(
    spreadsheetId=target_sheet_id,
    body={"requests": [{
        "updateSheetProperties": {
            "properties": {"sheetId": new_sheet_id, "title": "2025.03"},
            "fields": "title"
        }
    }]}
).execute()
```

### 셀 값 일괄 입력

```python
service.spreadsheets().values().batchUpdate(
    spreadsheetId=spreadsheet_id,
    body={
        "valueInputOption": "RAW",   # 수식 해석 없이 텍스트로 입력
        "data": [
            {"range": "'2025.03'!B3", "values": [["삼성전자"]]},
            {"range": "'2025.03'!C5", "values": [["1000000"]]},
        ]
    }
).execute()
# 반환: {"totalUpdatedCells": 2, ...}
```

> **주의**: 탭 이름에 공백이나 특수문자가 있을 때 작은따옴표로 감싸야 함.
> `'2025.03'!B3` 형식 사용 권장.

---

## 할당량 및 제한

| 제한 항목 | 값 |
|----------|-----|
| 읽기 요청 | 300 req/min (프로젝트), 60 req/min (사용자) |
| 쓰기 요청 | 300 req/min (프로젝트), 60 req/min (사용자) |
| batchUpdate 최대 요청 수 | 단일 호출당 1,000개 |
| 스프레드시트 최대 탭 수 | 200개 |

고객사 수가 많아 할당량 초과가 우려되는 경우 고객사 루프에 `time.sleep(1)` 추가를 고려.

---

## 자주 발생하는 오류

| 오류 코드 | 원인 | 해결 방법 |
|----------|------|----------|
| `403 PERMISSION_DENIED` | Service Account가 해당 파일의 편집자로 추가되지 않음 | Sheets 공유 설정에서 Service Account 이메일 편집자 추가 |
| `404 NOT_FOUND` | 잘못된 spreadsheet_id | Fixed 탭의 Key 컬럼 값 확인 |
| `400 INVALID_ARGUMENT` | 잘못된 범위 형식 | 탭 이름 특수문자 시 작은따옴표로 감싸기 |
| `429 RESOURCE_EXHAUSTED` | 할당량 초과 | 재시도 로직 또는 요청 간격 추가 |

# Agent: invoice-writer

단일 고객사의 인보이스 탭을 생성하고 변수 값을 입력하는 서브에이전트.

오케스트레이터(CLAUDE.md)가 고객사 루프에서 각 고객사마다 이 에이전트를 호출한다.

---

## 역할

고객사 1건을 완전히 처리하여 결과 JSON을 반환한다.

## 입력 (오케스트레이터가 프롬프트 인라인으로 전달)

```json
{
  "run_month": "2026/04",
  "tab_name": "2026.04",
  "log_path": "output/run_202604.log",
  "master_sheet_id": "1EVyVqFvntsWBYbeEO6Uxv2X6JbDBxP-er97WFd0U5SM",
  "template_sheet_id": 470125737,
  "client_row": {"CoCd": "C001", "[회사명]": "동국제약 주식회사", "[별칭]": "Dongkook", ...},
  "fixed_row": {"CoCd": "C001", "Key": "abc123", "[청구총액]": "3850000", "[고정비]": "3500000", "[추가브랜드]": "0", "[부가가치세]": "350000", ...},
  "variable_mapping": {
    "[회사명]":          {"type": "simple",  "source_tab": "Client", "source_col": "회사명"},
    "[청구총액]":        {"type": "simple",  "source_tab": "Fixed",  "source_col": "청구총액"},
    "[인보이스 청구년월]": {"type": "complex", "description": "인보이스가 청구되는 서비스 월로 YYYY/MM으로 표현", "example": "2026/04"},
    "[서비스 공급가액]":  {"type": "complex", "description": "Fixed![고정비]+Fixed![추가브랜드]", "example": "3500000"},
    "[지급기한]":        {"type": "complex", "description": "[인보이스일자] + 14일", "example": "2026/04/15"}
  }
}
```

## 출력

```json
{"status": "success", "sheet_url": "https://...", "new_sheet_id": 123456789, "reason": null}
{"status": "skipped", "sheet_url": null, "new_sheet_id": null, "reason": "탭 이미 존재: 2026.04"}
{"status": "error",   "sheet_url": null, "new_sheet_id": null, "reason": "탭 복제 실패: API 오류 메시지"}
```

`new_sheet_id`는 STEP 3-3에서 확보한 복제된 탭의 정수 sheetId. 오케스트레이터가 PDF 내보내기에 사용한다.

---

## 처리 절차

### STEP 3-1: 고객사 Key 확인

`fixed_row`에서 `Key` 값(고객사 Sheets 파일 ID) 추출 후 정제:

```
key = fixed_row["Key"].strip().rstrip("/")
```

- Key가 없거나 빈 문자열이면:
  - `run-logger` 호출: `--level SKIP --client {고객사명} --message "Key 없음 (Fixed 탭)"`
  - 반환: `{"status": "skipped", "reason": "Key 없음 (Fixed 탭)"}`

### STEP 3-2: 탭 중복 확인

`sheets-reader`로 고객사 Sheets 탭 목록 조회:

```bash
python .claude/skills/sheets-reader/scripts/read_sheets.py --spreadsheet-id {Key} --list-tabs
```

- `tabs` 목록에 `tab_name` (예: `2026.04`)이 이미 존재하면:
  - `run-logger` 호출: `--level SKIP --client {고객사명} --message "탭 이미 존재: {tab_name}"`
  - 반환: `{"status": "skipped", "reason": "탭 이미 존재: {tab_name}"}`

### STEP 3-3: Template 탭 복제

```bash
python .claude/skills/sheets-writer/scripts/copy_template_tab.py --master-sheet-id {master_sheet_id} --target-sheet-id {Key} --tab-name {tab_name} --template-sheet-id {template_sheet_id}
```

- 실패 시 MAX_RETRY(1)회 재시도.
- 재시도 후에도 실패하면: `run-logger` ERROR 기록 후 반환 `{"status": "error"}`
- 성공 시 `new_sheet_id`, `sheet_url` 보관.

### STEP 3-4: 변수 값 계산

#### 3-4-A: 복제된 탭의 플레이스홀더 위치 탐색

shell 파이프 인코딩 오류 방지를 위해 중간 결과를 파일로 저장한다.
모든 Python 호출에 `PYTHONUTF8=1` 환경변수를 설정한다.

```bash
# 표시값 읽기
PYTHONUTF8=1 python .claude/skills/sheets-reader/scripts/read_sheets.py \
  --spreadsheet-id {Key} --tab "{tab_name}" > /tmp/cells_{CoCd}.json

# 수식 원문 읽기 (수식 셀 제외용)
PYTHONUTF8=1 python .claude/skills/sheets-reader/scripts/read_sheets.py \
  --spreadsheet-id {Key} --tab "{tab_name}" --formula > /tmp/formulas_{CoCd}.json

# 플레이스홀더 탐색 (수식 셀 자동 제외)
PYTHONUTF8=1 python .claude/skills/variable-mapper/scripts/build_mapping.py \
  --find-placeholders \
  --cells-file /tmp/cells_{CoCd}.json \
  --formula-file /tmp/formulas_{CoCd}.json
```

결과 예시: `{"placeholders": {"C6": "[회사명]", "C12": "[인보이스 청구년월]", ...}}`

> **수식 셀 제외 규칙**: `=`로 시작하는 셀은 플레이스홀더 대상에서 자동 제외된다.
> Template의 B3(`=" - "&C11&...`), C16(`=H25`), H22(`=G20`) 등은 다른 셀 값이
> 채워지면 자동으로 계산되므로 직접 쓰지 않는다.

#### 3-4-B: 각 플레이스홀더의 실제 값 결정

`variable_mapping`의 `type`에 따라 처리 방식을 분리한다.

**type = "simple"** → 스크립트 조회
- `source_tab`이 `"Client"` → `client_row[source_col]`
- `source_tab`이 `"Fixed"` → `fixed_row[source_col]`

**type = "complex"** → LLM이 직접 계산
아래 컨텍스트를 바탕으로 값을 계산한다:

| 사용 가능한 데이터 | 내용 |
|------------------|------|
| `run_month` | 귀속월 (예: `2026/04`) |
| `client_row` | 해당 고객사의 Client 탭 전체 행 |
| `fixed_row` | 해당 고객사의 Fixed 탭 전체 행 |
| `description` | Instruction 탭의 `데이터` 컬럼 설명 |
| `example` | Instruction 탭의 `예시` 컬럼 참고값 |
| 이미 계산된 변수 값 | 앞서 결정된 변수의 실제값 (의존 관계 해소용) |

**complex 변수 계산 규칙:**

| 변수 | description | 계산 방법 |
|------|-------------|----------|
| `[인보이스 청구년월]` | YYYY/MM으로 표현 | `run_month` 그대로 |
| `[인보이스일자]` | 청구월의 초일, YYYY/MM/DD | `run_month`의 1일 (예: `2026/04/01`) |
| `[지급기한]` | `[인보이스일자] + 14일` | 인보이스일자 + 14일 (예: `2026/04/15`) |
| `[Type]` | `[인보이스 청구년월]-Service Fee` | `{run_month}-Service Fee` |
| `[서비스 기간]` | 초일 ~ 말일 | `2026/04/01 ~ 2026/04/30` |
| `[서비스 공급가액]` | `Fixed![고정비]+Fixed![추가브랜드]` | 아래 **화폐 포맷 규칙** 적용 |
| `[인보이스번호]` | `Client![별칭]-[인보이스청구년월]-Fixed-01` | `{client_row[별칭]}-{YYYYMM}-Fixed-01` |
| `[계좌번호]` | Currency 조건부 계좌번호 | `fixed_row["Currency"] == "USD"` → `"064-177713-56-00027"`, 그 외(KRW) → `"064-177713-04-036"` |

- 의존 관계가 있는 변수는 의존 대상을 먼저 계산한 후 사용한다.

**I14 SWIFT CODE 조건부 쓰기:**

`[계좌번호]` 변수 계산 후 Currency에 따라 I14 셀 값을 cells 딕셔너리에 추가한다:
- `fixed_row["Currency"] == "USD"` → `cells["I14"] = "SWIFT CODE : IBKOKRSE"`
- 그 외(KRW) → `cells["I14"] = ""` (빈 문자열로 기존 값 지움)

#### 화폐 포맷 규칙 (simple/complex 공통 적용)

`[서비스 공급가액]`, `[부가가치세액]`, `[청구총액]` 등 금액 변수는 **순수 정수(콤마 없음)**로
cells 딕셔너리에 저장한다. Sheets 숫자 포맷은 STEP 3-5에서 별도 API 호출로 적용한다.

**값 전처리 (소스가 Fixed 탭 셀인 경우):**
```python
raw = str(fixed_row["고정비"]).replace(",", "").strip()  # "3,500,000" → "3500000"
numeric = int(raw) if raw else 0
# cells 딕셔너리에는 numeric (정수) 그대로 저장
```

**[서비스 공급가액] 특이 사항 (복합 수식):**
```python
고정비 = int(str(fixed_row.get("고정비", "0")).replace(",", "").strip() or "0")
추가브랜드 = int(str(fixed_row.get("추가브랜드", "0")).replace(",", "").strip() or "0")
total = 고정비 + 추가브랜드  # 정수 그대로 저장
```

**금액 셀 목록 (포맷 적용 대상):**
플레이스홀더 탐색 결과에서 아래 변수명에 해당하는 셀 주소를 수집해둔다:
- `[서비스 공급가액]`, `[부가가치세액]`, `[청구총액]`
- 추가로 `H22` (=G20 수식 셀이지만 포맷 적용 필요)
- 추가로 `C16` (=H25 수식 셀이지만 포맷 적용 필요: USD → `$#,##0.00`, KRW → `₩#,##0`)

#### 3-4-C: 최종 cells 딕셔너리 구성

```json
{
  "B3": "동국제약 주식회사",
  "G20": 3500000,
  "H23": 350000,
  "H25": 3850000,
  "D7": "2026/04/01",
  ...
}
```

> 금액 셀에는 콤마 없는 정수를 저장. Sheets 포맷은 STEP 3-5에서 적용.

### STEP 3-5: 값 일괄 입력

#### 3-5-A: 값 쓰기

인보이스 값 입력은 **항상 `--user-entered` 플래그를 사용한다.**

```bash
PYTHONUTF8=1 python .claude/skills/sheets-writer/scripts/batch_write_cells.py \
  --spreadsheet-id {Key} \
  --tab-name "{tab_name}" \
  --user-entered \
  --cells '{셀주소: 실제값 딕셔너리 JSON}'
```

#### 3-5-B: 금액 셀 숫자 포맷 적용

값 쓰기 성공 후, 금액 셀에 통화 포맷을 적용한다.

- `--sheet-id`: STEP 3-3에서 확보한 `new_sheet_id` (정수)
- `--format-cells`: 포맷 적용할 셀 주소 목록 (쉼표 구분)
  - 플레이스홀더로 직접 쓴 금액 셀 + H22 (=G20 수식 셀) + C16 (=H25 수식 셀)
- `--currency`: `fixed_row["Currency"]` 값 (KRW 또는 USD)

```bash
PYTHONUTF8=1 python .claude/skills/sheets-writer/scripts/batch_write_cells.py \
  --spreadsheet-id {Key} \
  --tab-name "{tab_name}" \
  --sheet-id {new_sheet_id} \
  --cells '{}' \
  --format-cells "{금액셀주소들,쉼표구분}" \
  --currency {Currency}
```

**포맷 규칙:**
| Currency | 패턴 | 표시 예시 |
|----------|------|----------|
| `KRW` | `₩#,##0` | ₩3,500,000 (소수점 없음) |
| `USD` | `$#,##0.00` | $2,700.00 (소수점 2자리) |

- 실패 시 MAX_RETRY(1)회 재시도.
- 재시도 후에도 실패하면: `run-logger` ERROR 기록 후 반환 `{"status": "error"}`

### STEP 3-6: 결과 기록

```bash
python .claude/skills/run-logger/scripts/write_log.py --log-path {log_path} --level SUCCESS --client "{고객사명}" --message "탭: {tab_name} | URL: {sheet_url}"
```

반환: `{"status": "success", "sheet_url": "{sheet_url}"}`

---

## 환경변수 (오케스트레이터에서 상속)

- `GOOGLE_SERVICE_ACCOUNT_KEY`
- `MASTER_SHEET_ID`
- `MAX_RETRY` (기본값: 1)

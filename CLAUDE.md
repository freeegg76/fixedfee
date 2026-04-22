# 고정비 인보이스 자동화 에이전트

## 역할

매월 반복되는 고정비 인보이스 탭 생성 작업을 자동화하는 오케스트레이터.

운영자가 서비스 귀속월(`YYYY/MM`)을 입력하면:
1. 마스터 스프레드시트에서 고객·계약·템플릿·변수 정보를 수집
2. 변수 매핑 테이블 구성
3. 각 고객사마다 `invoice-writer` 서브에이전트를 호출하여 인보이스 탭 생성
4. 전체 실행 결과를 요약하여 운영자에게 보고

---

## 환경 설정

실행 전 아래 환경변수가 설정되어 있어야 한다:

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `GOOGLE_SERVICE_ACCOUNT_KEY` | Service Account JSON 키파일 경로 | 필수 |
| `MASTER_SHEET_ID` | 마스터 스프레드시트 ID | `1EVyVqFvntsWBYbeEO6Uxv2X6JbDBxP-er97WFd0U5SM` |
| `MAX_RETRY` | API 재시도 최대 횟수 | `1` |
| `PYTHONUTF8=1` | Python stdout/stdin UTF-8 강제 (Windows 필수) | 필수 |
| `GMAIL_FROM` | 발신자 표시 주소 | `info@forsit.co.kr` |
| `GMAIL_CC_ALWAYS` | 모든 초안에 강제 추가할 CC | `info@forsit.co.kr` |
| `OAUTH_CLIENT_SECRET` | OAuth 2.0 클라이언트 시크릿 파일 경로 | `c:/Dev/Fixed Fee/client_secret_600358750353-kqebejvfpp93u03ckl5rsnf7jkbmh6qs.apps.googleusercontent.com.json` |

모든 Python 스크립트 호출 시 `PYTHONUTF8=1`을 앞에 붙인다:
```bash
PYTHONUTF8=1 python .claude/skills/.../script.py ...
```

Python 의존 패키지: `google-auth`, `google-api-python-client`, `google-auth-httplib2`

---

## 마스터 스프레드시트 구조

**ID**: `1EVyVqFvntsWBYbeEO6Uxv2X6JbDBxP-er97WFd0U5SM`

| 탭명 | 역할 | sheetId | 핵심 컬럼 |
|------|------|---------|----------|
| `Client` | 고객사 목록 | `0` | `회사코드`(조인값), `회사명`, `주소`, `사업자등록번호`, `대표자`, `별칭`, `계약상황`(G컬럼) |
| `Fixed` | 고정비 계약 정보 | `787137051` | `CoCd`(조인값), `Name`, `Service`, `Currency`, `고정비`, `추가브랜드`, `부가가치세`, `청구총액`, `Key` |
| `Template` | 인보이스 양식 | **`470125737`** | `[변수명]` 플레이스홀더 셀 포함 |
| `Instruction` | 변수 정의 | `603560316` | `변수`, `데이터` (`탭명!컬럼명` 형식 또는 자연어/수식), `예시` |
| `Email` | 수신자 목록 | - | `회사코드`(A), `회사명`(B), `구분`(C: `To`/`CC`), `메일주소`(D) |

**조인 규칙**: Client.`회사코드` 값 = Fixed.`CoCd` 값 (헤더명은 다르지만 동일한 고객사 코드)

**Key 컬럼 주의**: 일부 행의 Key 값 끝에 `/`가 붙어 있음 → 사용 전 `rstrip("/")` 처리 필수

---

## 전체 워크플로우

### STEP 0 — 귀속월 입력 수신 및 유효성 검증

운영자에게 귀속월 입력 요청:

```
서비스 귀속월을 입력하세요 (형식: YYYY/MM):
```

검증 규칙:
- 형식: `YYYY/MM` (슬래시 포함 7자리)
- 월 범위: `01` ~ `12`
- 실패 시: 즉시 중단, 재입력 요청

귀속월 파생값 계산:
- `tab_name` = `YYYY.MM` (슬래시 → 점, 예: `2025/03` → `2025.03`)
- `month_key` = `YYYYMM` (슬래시 제거, 예: `2025/03` → `202503`)
- `log_path` = `output/run_{month_key}.log`
- `summary_path` = `output/summary_{month_key}.json`

### STEP 1 — 마스터 스프레드시트 데이터 수집

아래 4개를 순서대로 수집한다. 실패 시 1회 재시도, 재시도 후에도 실패하면 전체 중단.

**1-A. Client 탭 읽기**
```bash
python .claude/skills/sheets-reader/scripts/read_sheets.py \
  --spreadsheet-id $MASTER_SHEET_ID --tab "Client"
```
→ `client_rows` (헤더 포함 전체 행)

**1-B. Fixed 탭 읽기**
```bash
python .claude/skills/sheets-reader/scripts/read_sheets.py \
  --spreadsheet-id $MASTER_SHEET_ID --tab "Fixed"
```
→ `fixed_rows` (헤더 포함 전체 행)

**1-C. Template 탭 sheetId**

고정값 사용 (별도 API 조회 불필요):
```
template_sheet_id = 470125737
```

**1-D. Instruction 탭 읽기**
```bash
python .claude/skills/sheets-reader/scripts/read_sheets.py \
  --spreadsheet-id $MASTER_SHEET_ID --tab "Instruction"
```
→ `instruction_rows` (헤더 포함 전체 행)

**1-E. Email 탭 읽기**
```bash
python .claude/skills/sheets-reader/scripts/read_sheets.py \
  --spreadsheet-id $MASTER_SHEET_ID --tab "Email"
```
→ `email_rows` (헤더 포함 전체 행)

성공 기준: 5개 모두 수집 완료, `client_rows` 데이터 행 수 ≥ 1

### STEP 2 — 변수 매핑 테이블 구성

```bash
python .claude/skills/variable-mapper/scripts/build_mapping.py --instruction-json '{instruction_rows JSON}'
```

각 변수는 두 가지 유형으로 분류된다:
- **simple**: `탭명![컬럼명]` 형식 → 스크립트로 행 데이터에서 직접 조회
- **complex**: 자연어 설명, 날짜 계산, 수식, 다중 참조 → invoice-writer가 LLM으로 계산

→ `variable_mapping` (딕셔너리, simple/complex 유형 포함)

### STEP 3 — 고객사별 루프 처리

START 로그 기록:
```bash
python .claude/skills/run-logger/scripts/write_log.py \
  --log-path {log_path} --level START --message "귀속월: {run_month}"
```

**데이터 준비**: `client_rows`와 `fixed_rows`를 인메모리 조인하여 각 고객사의 `client_row` + `fixed_row` 쌍을 구성한다.

조인 규칙:
- Client 탭 첫 번째 컬럼(`회사코드`)과 Fixed 탭 `CoCd` 컬럼의 **값**이 일치하는 행을 매핑
- 컬럼 헤더명이 다르므로 헤더명이 아닌 값(예: `1000`, `1100`)으로 매칭
- Fixed 탭에 매핑되는 행이 없으면 해당 고객사는 SKIP

**계약상황 필터**: Client 탭 G컬럼(`계약상황`) 값이 `"유효"`인 행만 처리 대상으로 포함한다.
- `계약상황 != "유효"` 인 행은 루프에서 완전히 제외 (SKIP 로그 불필요, 단순 미포함)
- `total` 집계 기준도 이 필터 적용 후 건수로 산정한다.

**Fixed 탭 Key 컬럼 정제**: Key 값 끝에 `/`가 붙어 있는 경우 제거 후 사용
- 예: `"1tPR4Tr-...MgD8/"` → `"1tPR4Tr-...MgD8"`

**루프**: Client 탭 데이터 행마다 `invoice-writer` 서브에이전트 호출:

```
Task: .claude/agents/invoice-writer/AGENT.md 지침에 따라 아래 고객사의 인보이스 탭을 생성하라.

입력 데이터:
{
  "run_month": "{run_month}",
  "tab_name": "{tab_name}",
  "log_path": "{log_path}",
  "master_sheet_id": "1EVyVqFvntsWBYbeEO6Uxv2X6JbDBxP-er97WFd0U5SM",
  "template_sheet_id": 470125737,
  "client_row": {client_row},
  "fixed_row": {fixed_row},
  "variable_mapping": {variable_mapping}
}

variable_mapping의 type이 "simple"인 변수는 client_row/fixed_row에서 직접 조회하고,
type이 "complex"인 변수는 description과 example을 참고하여 LLM이 직접 계산한다.
```

각 호출 결과(`status`, `sheet_url`, `reason`)를 `results` 목록에 추가.

**invoice-writer가 `status == "success"`를 반환한 경우에만** 아래 메일 초안 생성을 진행한다.

#### 메일 초안 생성 (인보이스 성공 시)

**① PDF 내보내기**

invoice-writer 반환값에서 `new_sheet_id` (복제된 탭의 정수 sheetId)를 받아 PDF를 내보낸다.

```
pdf_filename = f"{client_row['별칭']} Fixed Fee Invoice {month_key}.pdf"
pdf_path     = f"output/{pdf_filename}"
```

```bash
PYTHONUTF8=1 GOOGLE_SERVICE_ACCOUNT_KEY="c:/Dev/Fixed Fee/credentials.json" \
python .claude/skills/gmail-draft/scripts/export_pdf.py \
  --spreadsheet-id {Key} \
  --sheet-id {new_sheet_id} \
  --output "{pdf_path}"
```

- 실패 시 MAX_RETRY(1)회 재시도.
- 재시도 후에도 실패하면: `run-logger` ERROR 기록, `email_draft: "error"` 표시 후 해당 고객사 메일 초안 생성 중단.

**② 수신자 구성**

`email_rows`에서 현재 고객사 `회사코드`와 일치하는 행을 필터링한다.
- `구분 == "To"` 인 행의 `메일주소`를 쉼표로 결합 → `to_str`
- `구분 == "CC"` 인 행의 `메일주소`를 쉼표로 결합 → `cc_str`

**③ 메일 제목·본문 구성**

```
subject = f"[아마존_Invoice] {client_row['별칭']} Fixed Fee invoice {month_key}"
body    = "안녕하세요 폴싯 빌링팀입니다. \n\n고정비 {month_key} invoice를 송부드립니다. \n\n폴싯 빌링팀 드림"
```

(`month_key` = `YYYYMM` 형식, 예: `202605`)

**④ Gmail 초안 저장 (PDF 첨부)**

```bash
PYTHONUTF8=1 python .claude/skills/gmail-draft/scripts/create_draft.py \
  --to "{to_str}" \
  --cc "{cc_str}" \
  --subject "{subject}" \
  --body "{body}" \
  --attachment "{pdf_path}"
```

- 실패 시 MAX_RETRY(1)회 재시도.
- 재시도 후에도 실패하면: `run-logger` ERROR 기록, 해당 고객사 결과에 `email_draft: "error"` 표시 (인보이스 자체는 success 유지)
- 성공 시 결과에 `email_draft: "success"` 표시.

### STEP 4 — 전체 실행 요약 생성

루프 완료 후 집계:
- `total` = `계약상황 == "유효"` 인 Client 행 수 (처리 시도 건수)
- `success` = status == "success" 수
- `skipped` = status == "skipped" 수
- `failed` = status == "error" 수
- `email_drafted` = email_draft == "success" 수
- `email_failed` = email_draft == "error" 수

END 로그 기록:
```bash
python .claude/skills/run-logger/scripts/write_log.py \
  --log-path {log_path} --level END \
  --message "총 {total}건 | 성공 {success} / 스킵 {skipped} / 실패 {failed}"
```

Summary JSON 작성:
```bash
python .claude/skills/run-logger/scripts/write_log.py \
  --summary-path {summary_path} \
  --summary-json '{집계 결과 JSON}'
```

운영자에게 결과 보고:
```
=== 고정비 인보이스 자동화 완료 ===
귀속월: {run_month}
총 처리: {total}건 | 성공: {success} | 스킵: {skipped} | 실패: {failed}
메일 초안: 생성 {email_drafted} | 실패 {email_failed}

[실패 목록]
- {고객사명}: {reason}
...

[메일 초안 실패 목록]
- {고객사명}: {email 오류 내용}
...

로그: {log_path}
요약: {summary_path}
```

---

## 실패 처리 정책

| 실패 시점 | 처리 방식 |
|----------|----------|
| 귀속월 형식 오류 | 즉시 중단, 재입력 요청 |
| 마스터 시트 읽기 실패 | 재시도 1회 → 전체 중단 |
| 변수 매핑 파싱 오류 | 에스컬레이션 → 전체 중단 |
| 고객사 Key 없음 | 해당 고객사 SKIP + 로그 |
| 탭 이미 존재 | 해당 고객사 SKIP + 로그 |
| 탭 복제 실패 | 재시도 1회 → 해당 고객사 ERROR + 로그 |
| 값 입력 실패 | 재시도 1회 → 해당 고객사 ERROR + 로그 |
| 계약상황 ≠ "유효" | 루프에서 제외 (로그 불필요) |
| 메일 초안 저장 실패 | 재시도 1회 → email_draft ERROR + 로그 (인보이스 결과는 success 유지) |

---

## 스킬 참조

| 스킬 | 경로 |
|------|------|
| sheets-reader | `.claude/skills/sheets-reader/SKILL.md` |
| sheets-writer | `.claude/skills/sheets-writer/SKILL.md` |
| variable-mapper | `.claude/skills/variable-mapper/SKILL.md` |
| run-logger | `.claude/skills/run-logger/SKILL.md` |
| gmail-draft | `.claude/skills/gmail-draft/scripts/create_draft.py` |

## 서브에이전트 참조

| 에이전트 | 경로 |
|---------|------|
| invoice-writer | `.claude/agents/invoice-writer/AGENT.md` |

## 설계 문서

`fixed-invoice-agent-design.md`

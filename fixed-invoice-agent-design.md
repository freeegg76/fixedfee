# 고정비 인보이스 자동화 에이전트 설계서

> Claude Code 구현 참조용 계획서 | 작성일: 2025 | 인터뷰 보완: 2026-04-21

---

## 1. 작업 컨텍스트

### 1.1 배경 및 목적

매월 반복되는 고정비 인보이스 생성 작업을 자동화한다. 운영자가 서비스 귀속월(YYYY/MM)을 입력하면, 에이전트가 마스터 스프레드시트의 고객·계약 정보를 읽어 각 고객사의 인보이스 시트에 해당 월의 탭을 자동 생성·입력한다.

### 1.2 범위

| 항목 | 포함 | 제외 |
|------|------|------|
| 인보이스 시트 탭 생성 | ✅ | 인보이스 발송(이메일 등) |
| Template 서식 복제 | ✅ | 인보이스 PDF 변환 |
| 변수 값 자동 입력 | ✅ | 고정비 외 청구 항목 처리 |
| 실패 로깅 | ✅ | 승인 워크플로우 |

### 1.3 입출력 정의

**입력**
- 서비스 귀속월: `YYYY/MM` 형식 (운영자 입력)
- 마스터 스프레드시트 (고정 키: `1EVyVqFvntsWBYbeEO6Uxv2X6JbDBxP-er97WFd0U5SM`)

**출력**
- 각 고객사 Google Sheets 파일에 `YYYY.MM` 탭 생성 완료
- 실행 로그 파일: `output/run_YYYYMM.log`
- 실행 결과 요약: `output/summary_YYYYMM.json`

### 1.4 마스터 스프레드시트 구조

| 탭명 | 역할 | 주요 컬럼 |
|------|------|----------|
| `Client` | 고객사 목록 | `CoCd`(고객사 ID, 조인 키), 기타 고객사 정보 |
| `Fixed` | 고정비 계약 정보 | `CoCd`(조인 키), `Key`(고객사 Google Sheets 파일 ID), 청구 금액, 계약 조건 |
| `Template` | 인보이스 양식 | 셀 구조·수식·서식, `[변수명]` 플레이스홀더 포함 |
| `Instruction` | 템플릿 변수 정의 | `변수`(변수명), `데이터`(소스 참조), `예시`(예시값) |

#### Instruction 탭 상세

| 컬럼 | 형식 | 설명 | 예시 |
|------|------|------|------|
| `변수` | 텍스트 | 변수 식별자 (Template 플레이스홀더와 1:1 대응) | `Client_name` |
| `데이터` | `탭명!컬럼명` | 값을 가져올 소스 위치 (파싱 가능한 구조화 형식) | `Fixed!CoCd` |
| `예시` | 텍스트 | 참고용 예시값 (실행 시 미사용) | `삼성전자` |

#### Template 탭 플레이스홀더 규칙

- 형식: `[변수명]` (대괄호로 감싼 변수명)
- 매핑: Instruction `변수` 컬럼값에 `[]`를 덧붙이면 Template 셀 플레이스홀더와 일치
  - 예: Instruction `변수` = `Client_name` → Template 셀 = `[Client_name]`
- 탭 복제 후 플레이스홀더 텍스트를 스캔하여 실제 값으로 교체

#### Template 탭 위치

- **마스터 스프레드시트** 안에 존재
- `copyTo` API로 각 고객사 Sheets 파일에 복사 후 `YYYY.MM`으로 이름 변경

### 1.5 제약 조건

- Google Sheets API 인증: Service Account (키파일 경로는 환경변수로 관리)
- 동일 귀속월 탭이 이미 존재하는 경우: 덮어쓰지 않고 스킵 + 로그 기록
- 고객사별 실패는 해당 건만 스킵, 나머지 고객사는 계속 처리
- Template 복제 수준: 값 + 서식(색상, 폰트, 테두리) 모두 복제
- Service Account는 마스터 스프레드시트 및 모든 고객사 Sheets 파일에 편집 권한 부여 완료

### 1.6 용어 정의

| 용어 | 정의 |
|------|------|
| 귀속월 | 청구 서비스의 제공 기준 월 (≠ 발행일) |
| `CoCd` | Client·Fixed 탭에서 고객사를 식별하는 공통 조인 키 |
| `Key` | Fixed 탭에서 고객사 Google Sheets 파일 ID를 저장하는 컬럼 |
| 변수 | Instruction 탭 `변수` 컬럼에 정의된 치환 대상 식별자 |
| 플레이스홀더 | Template 탭 셀 안에 `[변수명]` 형태로 삽입된 치환 마커 |
| 인보이스 시트 | 고객사별로 존재하는 개별 Google Sheets 파일 |

---

## 2. 워크플로우 정의

### 2.1 전체 흐름

```
[START]
   │
   ▼
[STEP 0] 귀속월 입력 수신 및 유효성 검증
   │  성공 기준: YYYY/MM 형식, 유효한 연월(월 01~12)
   │  실패 시: 즉시 중단 + 사용자에게 재입력 요청
   │
   ▼
[STEP 1] 마스터 스프레드시트 데이터 수집
   │  1-A. Client 탭 전체 읽기
   │  1-B. Fixed 탭 전체 읽기
   │  1-C. Template 탭 sheetId 확인 (copyTo 용)
   │  1-D. Instruction 탭 전체 읽기
   │  성공 기준: 4개 탭 모두 읽기 성공, Client 행 수 ≥ 1
   │  실패 시: 자동 재시도 1회 → 실패 시 즉시 중단
   │
   ▼
[STEP 2] 변수 매핑 테이블 구성  ← 스크립트 처리
   │  Instruction 탭의 변수/데이터 컬럼을 파싱하여
   │  {변수명 → (소스탭, 소스컬럼)} 매핑 딕셔너리 생성
   │  형식: 데이터 컬럼값 "탭명!컬럼명"을 "!" 기준으로 분리
   │  성공 기준: 모든 변수에 소스탭·소스컬럼 매핑 완료
   │  실패 시: 파싱 불가 변수 목록 로그 → 에스컬레이션
   │
   ▼
[STEP 3] 고객사별 루프 처리  ── Client 탭 첫 행 ~ 마지막 행
   │
   ├─▶ [STEP 3-1] 고객사 정보 및 계약 정보 조회  ← 스크립트
   │       Client 탭 CoCd → Fixed 탭 CoCd 조인으로 Key(파일 ID) 추출
   │       성공 기준: Key(파일 ID) 값 존재
   │       실패 시: 스킵 + 로그 ("Key 없음: {고객사명}")
   │
   ├─▶ [STEP 3-2] 기존 탭 중복 확인  ← 스크립트
   │       고객사 Sheets 파일에서 YYYY.MM 탭 존재 여부 확인
   │       존재하면: 스킵 + 로그 ("탭 이미 존재: {고객사명} / {YYYY.MM}")
   │
   ├─▶ [STEP 3-3] Template 탭 복제  ← 스크립트
   │       마스터의 Template sheetId로 copyTo API 호출 (대상: 고객사 Sheets)
   │       복제 후 탭 이름을 YYYY.MM으로 변경
   │       성공 기준: 새 sheetId 반환 확인
   │       실패 시: 자동 재시도 1회 → 스킵 + 로그
   │
   ├─▶ [STEP 3-4] 변수 값 계산  ← 스크립트
   │       STEP 2 매핑 테이블 + 고객사 CoCd로
   │       각 변수의 실제 값을 인메모리 데이터에서 직접 참조
   │       결과: {변수명 → 실제값} 딕셔너리
   │
   ├─▶ [STEP 3-5] 플레이스홀더 교체 및 값 일괄 입력  ← 스크립트
   │       새 탭의 셀을 스캔하여 [변수명] 패턴 탐색
   │       batchUpdate API로 실제 값으로 교체 입력
   │       성공 기준: 필수 변수 셀 모두 입력 완료
   │       실패 시: 자동 재시도 1회 → 스킵 + 로그
   │
   └─▶ [STEP 3-6] 고객사 결과 기록  ← 스크립트
           성공/실패 여부, 탭 URL, 실패 사유를 로그에 추가
   │
   ▼
[STEP 4] 전체 실행 요약 생성  ← LLM 판단 영역
   │  총 처리 수, 성공 수, 실패 목록, 스킵 목록을 요약
   │  성공 기준: summary JSON 파일 생성 완료
   │
   ▼
[END] 운영자에게 결과 보고
```

### 2.2 LLM 판단 영역 vs 스크립트 처리 영역

> **아키텍처 변경**: Instruction 탭의 `데이터` 컬럼이 `탭명!컬럼명` 구조화 형식임이 확인되어
> STEP 2·3-4가 순수 스크립트로 처리 가능해졌다. LLM 관여는 STEP 4 요약 생성으로 최소화된다.

| 단계 | 처리 주체 | 이유 |
|------|----------|------|
| STEP 2: 변수 매핑 구성 | **스크립트** | `탭명!컬럼명` 형식이므로 "!" 기준 파싱으로 결정론적 처리 가능 |
| STEP 3-4: 변수 값 계산 | **스크립트** | 단순 컬럼 참조 (인메모리 데이터 딕셔너리 조회) |
| STEP 4: 실행 요약 생성 | **LLM** | 실패 원인 분류 및 자연어 요약 |
| STEP 1: API 데이터 읽기 | **스크립트** | 결정론적 I/O |
| STEP 3-2: 중복 확인 | **스크립트** | 탭 이름 비교, 결정론적 |
| STEP 3-3: 탭 복제 | **스크립트** | Google Sheets copyTo API 호출 |
| STEP 3-5: 값 입력 | **스크립트** | batchUpdate API 호출 |
| STEP 3-6: 결과 기록 | **스크립트** | 파일 쓰기 |

### 2.3 분기 조건 정리

| 조건 | 처리 방식 |
|------|----------|
| 입력 귀속월 형식 오류 | 즉시 중단, 사용자 재입력 요청 |
| 마스터 시트 읽기 실패 | 재시도 1회 → 전체 중단 |
| 변수 매핑 파싱 불가 (`탭명!컬럼명` 형식 위반) | 해당 변수 목록 로그 → 에스컬레이션 |
| 고객사 Key 없음 (CoCd 조인 실패 또는 Key 컬럼 공백) | 해당 고객사 스킵 + 로그 |
| 탭 이미 존재 | 해당 고객사 스킵 + 로그 |
| 탭 복제 실패 | 재시도 1회 → 스킵 + 로그 |
| 값 입력 실패 | 재시도 1회 → 스킵 + 로그 |

---

## 3. 구현 스펙

### 3.1 폴더 구조

```
c:\Dev\Fixed Fee\
  ├── CLAUDE.md                              # 메인 에이전트 지침 (오케스트레이터)
  ├── fixed-invoice-agent-design.md          # 이 설계서
  ├── .claude\
  │   ├── skills\
  │   │   ├── sheets-reader\
  │   │   │   ├── SKILL.md
  │   │   │   └── scripts\
  │   │   │       └── read_sheets.py         # Sheets 탭 데이터 읽기
  │   │   ├── sheets-writer\
  │   │   │   ├── SKILL.md
  │   │   │   └── scripts\
  │   │   │       ├── copy_template_tab.py   # Template 탭 복제 (서식 포함)
  │   │   │       └── batch_write_cells.py   # 플레이스홀더 스캔 + 셀 값 일괄 입력
  │   │   ├── variable-mapper\
  │   │   │   ├── SKILL.md
  │   │   │   └── scripts\
  │   │   │       └── build_mapping.py       # Instruction 탭 파싱 → 매핑 테이블 생성
  │   │   └── run-logger\
  │   │       ├── SKILL.md
  │   │       └── scripts\
  │   │           └── write_log.py           # 로그·요약 파일 기록
  │   └── agents\
  │       └── invoice-writer\
  │           └── AGENT.md                   # 고객사별 인보이스 생성 서브에이전트
  ├── output\
  │   ├── run_YYYYMM.log                     # 실행 로그 (append)
  │   └── summary_YYYYMM.json                # 전체 실행 결과 요약
  └── docs\
      └── sheets_api_guide.md                # Google Sheets API 참고 메모
```

> **변경**: `variable-mapper` 스킬이 LLM 참조 문서 기반에서 Python 스크립트 기반으로 전환됨

### 3.2 CLAUDE.md 핵심 섹션 목록

- 역할 정의: 오케스트레이터, 전체 워크플로우 관리
- 입력 처리: 귀속월 파싱 및 유효성 검증 규칙
- 마스터 시트 접근 정보: 스프레드시트 ID(`1EVyVqFvntsWBYbeEO6Uxv2X6JbDBxP-er97WFd0U5SM`), 탭명 목록
- 스킬 호출 순서 및 조건
- 서브에이전트 위임 조건 및 데이터 전달 방식
- 실패 처리 정책 (재시도 횟수, 스킵 조건)
- 최종 보고 형식

### 3.3 에이전트 구조

**단일 오케스트레이터 + 1개 서브에이전트** 구조를 채택한다.

```
CLAUDE.md (오케스트레이터)
  │
  ├── STEP 0~2: 오케스트레이터 직접 처리
  │     (귀속월 검증, 마스터 시트 읽기, 변수 매핑 테이블 구성)
  │
  └── STEP 3 (고객사 루프): invoice-writer 서브에이전트 위임
        고객사 1건당 1회 호출
        컨텍스트에는 해당 고객사 데이터만 전달
```

**서브에이전트 분리 이유**: STEP 3의 고객사별 처리는 독립된 작업 단위이며, 루프 반복 시 오케스트레이터 컨텍스트에 불필요한 고객사별 중간 데이터가 누적되는 것을 방지하기 위해 분리한다.

### 3.4 서브에이전트: invoice-writer

| 항목 | 내용 |
|------|------|
| **이름** | `invoice-writer` |
| **역할** | 단일 고객사의 인보이스 탭 생성 및 값 입력 |
| **트리거 조건** | 오케스트레이터가 고객사 루프의 각 고객사 처리 시 호출 |
| **입력** | 귀속월, 고객사 행(Client), 계약 행(Fixed), 변수 매핑 테이블, 마스터 스프레드시트 ID, 고객사 Sheets 파일 ID |
| **출력** | `{status: "success"/"skip"/"error", sheet_url, reason}` JSON |
| **데이터 전달 방식** | 프롬프트 인라인 (고객사 1건 데이터는 소량) |
| **참조 스킬** | `sheets-reader`, `sheets-writer`, `run-logger` |

### 3.5 스킬 목록

| 스킬명 | 역할 | 구현 방식 | 트리거 조건 |
|--------|------|----------|------------|
| `sheets-reader` | Google Sheets 탭 데이터 읽기 | Python 스크립트 | STEP 1 마스터 읽기, STEP 3-2 탭 존재 확인 |
| `sheets-writer` | Template 탭 복제 + 플레이스홀더 교체 입력 | Python 스크립트 | STEP 3-3 탭 복제, STEP 3-5 값 입력 |
| `variable-mapper` | Instruction 탭 `탭명!컬럼명` 파싱 → 매핑 테이블 생성 | Python 스크립트 | STEP 2 |
| `run-logger` | 로그 append 및 summary JSON 생성/업데이트 | Python 스크립트 | STEP 3-6 결과 기록, STEP 4 요약 생성 |

### 3.6 주요 산출물 파일 형식

**실행 로그** (`output/run_YYYYMM.log`)
```
[2025-03-01 09:00:01] START | 귀속월: 2025/03
[2025-03-01 09:00:03] SUCCESS | 고객사A | 탭: 2025.03 | URL: https://...
[2025-03-01 09:00:07] SKIP | 고객사B | 사유: 탭 이미 존재
[2025-03-01 09:00:09] ERROR | 고객사C | 사유: Key 없음 (Fixed 탭)
[2025-03-01 09:00:15] END | 총 5건 | 성공 3 / 스킵 1 / 실패 1
```

**실행 결과 요약** (`output/summary_YYYYMM.json`)
```json
{
  "run_month": "2025/03",
  "executed_at": "2025-03-01T09:00:15",
  "total": 5,
  "success": 3,
  "skipped": 1,
  "failed": 1,
  "results": [
    {
      "client": "고객사A",
      "status": "success",
      "sheet_id": "abc123",
      "tab_name": "2025.03",
      "sheet_url": "https://docs.google.com/spreadsheets/d/abc123"
    },
    {
      "client": "고객사B",
      "status": "skipped",
      "reason": "탭 이미 존재: 2025.03"
    },
    {
      "client": "고객사C",
      "status": "failed",
      "reason": "Fixed 탭에 Key 없음 (CoCd: C001)"
    }
  ]
}
```

### 3.7 환경 변수 및 설정

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `GOOGLE_SERVICE_ACCOUNT_KEY` | Service Account JSON 키파일 경로 | 필수 |
| `MASTER_SHEET_ID` | 마스터 스프레드시트 ID | `1EVyVqFvntsWBYbeEO6Uxv2X6JbDBxP-er97WFd0U5SM` |
| `MAX_RETRY` | API 재시도 최대 횟수 | `1` |

**실행 환경**
- Python: conda 환경 (환경명은 `.env` 또는 `conda activate <name>` 후 실행)
- 필수 패키지: `google-auth`, `google-api-python-client`, `google-auth-httplib2`

### 3.8 Google Sheets API 주요 사용 메서드

| 작업 | API 메서드 |
|------|-----------|
| 탭 데이터 읽기 | `spreadsheets.values.get` |
| 탭 sheetId 조회 | `spreadsheets.get` (fields: `sheets.properties`) |
| Template 탭 복제 | `spreadsheets.sheets.copyTo` |
| 탭 이름 변경 | `spreadsheets.batchUpdate` (UpdateSheetPropertiesRequest) |
| 탭 셀 값 읽기 (플레이스홀더 스캔) | `spreadsheets.values.get` (전체 범위) |
| 셀 값 일괄 입력 | `spreadsheets.values.batchUpdate` |
| 탭 목록 확인 (중복 체크) | `spreadsheets.get` (fields: `sheets.properties`) |

### 3.9 variable-mapper 스크립트 핵심 로직

```python
# Instruction 탭 파싱 → 매핑 테이블
def build_mapping(instruction_rows: list[list]) -> dict:
    """
    instruction_rows: [헤더행, 데이터행, ...]
    반환: {변수명: {"source_tab": str, "source_col": str}}
    """
    headers = instruction_rows[0]  # ["변수", "데이터", "예시"]
    var_idx = headers.index("변수")
    data_idx = headers.index("데이터")

    mapping = {}
    for row in instruction_rows[1:]:
        var_name = row[var_idx]
        data_ref = row[data_idx]          # 예: "Fixed!CoCd"
        tab, col = data_ref.split("!", 1)
        mapping[var_name] = {"source_tab": tab, "source_col": col}
    return mapping

# 플레이스홀더 교체 셀 찾기
def find_placeholders(cell_values: list[list]) -> dict:
    """
    반환: {"A1": "Client_name", "B5": "Amount", ...}
    """
    import re
    found = {}
    for r_idx, row in enumerate(cell_values):
        for c_idx, cell in enumerate(row):
            match = re.search(r'\[(\w+)\]', str(cell))
            if match:
                col_letter = col_index_to_letter(c_idx)
                cell_addr = f"{col_letter}{r_idx + 1}"
                found[cell_addr] = match.group(1)
    return found
```

---

## 4. 검증 계획

| 단계 | 검증 유형 | 성공 기준 |
|------|----------|----------|
| STEP 0 입력 검증 | 규칙 기반 | YYYY/MM 형식, 유효한 월(01~12) |
| STEP 1 데이터 수집 | 스키마 검증 | 4개 탭 응답 수신, Client 행 수 ≥ 1 |
| STEP 2 변수 매핑 | 파싱 검증 | 전체 변수의 `탭명!컬럼명` 파싱 성공 |
| STEP 3-2 중복 확인 | 규칙 기반 | 탭명 존재 여부 Boolean 반환 |
| STEP 3-3 탭 복제 | 스키마 검증 | 새 sheetId 반환 확인 |
| STEP 3-5 값 입력 | 규칙 기반 | 플레이스홀더 수 = 입력 완료 셀 수 |
| STEP 4 요약 | 규칙 기반 | summary JSON 파일 생성, total = success + skipped + failed |

---

## 5. 주요 설계 결정 근거

| 결정 사항 | 선택 | 근거 |
|----------|------|------|
| 에이전트 구조 | 오케스트레이터 + 1 서브에이전트 | 고객사 루프 반복 시 컨텍스트 오염 방지 |
| 탭 복제 방식 | `copyTo` API | 서식·수식 포함 복제가 보장되는 공식 API |
| 데이터 전달 | 프롬프트 인라인 (고객사 단위) | 고객사 1건 데이터는 소량, 파일 왕복 불필요 |
| 실패 처리 | 스킵 + 로그 | 1건 실패가 전체 배치를 중단시키지 않도록 |
| 중복 탭 처리 | 덮어쓰지 않고 스킵 | 기존 수동 수정 내용 보호 |
| 변수 매핑 처리 | 순수 스크립트 | Instruction `데이터` 컬럼이 `탭명!컬럼명` 구조화 형식임이 확인됨 → LLM 불필요 |
| 플레이스홀더 형식 | `[변수명]` | 실제 시트 확인 결과 대괄호 형식 사용 중 |
| 조인 키 | `CoCd` | Client·Fixed 탭 공통 컬럼명 확인 |

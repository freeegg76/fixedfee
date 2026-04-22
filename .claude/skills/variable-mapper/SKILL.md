# Skill: variable-mapper

Instruction 탭 파싱 → 변수 매핑 테이블 생성, 복제된 탭에서 플레이스홀더 위치 탐색.

## 스크립트

`.claude/skills/variable-mapper/scripts/build_mapping.py`

---

## 모드 1: 매핑 테이블 생성 (STEP 2)

Instruction 탭의 `변수 / 데이터 / 예시` 컬럼을 파싱하여
`{변수명 → {source_tab, source_col}}` 딕셔너리를 생성한다.

`데이터` 컬럼 형식: `탭명!컬럼명` (예: `Fixed!CoCd`, `Client!회사명`)

### 호출 방법

```bash
# 먼저 Instruction 탭 읽기
INSTRUCTION_JSON=$(python .claude/skills/sheets-reader/scripts/read_sheets.py \
  --spreadsheet-id $MASTER_SHEET_ID --tab "Instruction")

# 매핑 테이블 생성
python .claude/skills/variable-mapper/scripts/build_mapping.py \
  --instruction-json "$INSTRUCTION_JSON"
```

### 출력 형식

```json
{
  "mapping": {
    "Client_name": {"source_tab": "Client", "source_col": "회사명"},
    "CoCd":        {"source_tab": "Fixed",  "source_col": "CoCd"},
    "Amount":      {"source_tab": "Fixed",  "source_col": "청구금액"}
  },
  "parse_errors": []
}
```

- `parse_errors`가 비어 있지 않으면 에스컬레이션 (운영자 확인 필요)

---

## 모드 2: 플레이스홀더 탐색 (STEP 3-5 전처리)

복제된 탭의 셀 값을 스캔하여 `[변수명]` 패턴을 찾는다.
수식 셀(`=`로 시작)은 자동으로 제외한다 — 다른 셀이 채워지면 자동 계산되기 때문.

### 호출 방법

shell 파이프 인코딩 문제로 반드시 **파일 경유** 방식을 사용한다.

```bash
# 1. 표시값 읽기 → 파일 저장
PYTHONUTF8=1 python .claude/skills/sheets-reader/scripts/read_sheets.py \
  --spreadsheet-id $CLIENT_SHEET_KEY --tab "2026.04" > /tmp/cells.json

# 2. 수식 원문 읽기 → 파일 저장 (수식 셀 제외용)
PYTHONUTF8=1 python .claude/skills/sheets-reader/scripts/read_sheets.py \
  --spreadsheet-id $CLIENT_SHEET_KEY --tab "2026.04" --formula > /tmp/formulas.json

# 3. 플레이스홀더 탐색 (수식 셀 자동 제외)
PYTHONUTF8=1 python .claude/skills/variable-mapper/scripts/build_mapping.py \
  --find-placeholders \
  --cells-file /tmp/cells.json \
  --formula-file /tmp/formulas.json
```

### 출력 형식

```json
{
  "placeholders": {
    "C6": "[회사명]",
    "C12": "[인보이스 청구년월]",
    "C13": "[인보이스번호]",
    "C14": "[인보이스일자]",
    "C15": "[지급기한]",
    "B20": "[Type]",
    "D20": "[서비스 기간]",
    "G20": "[서비스 공급가액]",
    "H23": "[부가가치세액]",
    "H25": "[청구총액]"
  }
}
```

> Template 기준 수식 셀로 자동 제외되는 셀: `B3`, `C16`(`=H25`), `H22`(`=G20`)

---

## STEP 3-4 값 계산 절차

플레이스홀더 탐색 결과와 매핑 테이블을 결합하여 `{셀주소: 실제값}` 딕셔너리를 구성:

```
for 셀주소, 변수명 in placeholders.items():
    mapping = variable_mapping[변수명]
    source_tab_data = in_memory_data[mapping["source_tab"]]   # STEP 1에서 읽은 데이터
    실제값 = source_tab_data[현재_고객사_행][mapping["source_col"]]
    cells[셀주소] = 실제값
```

이 값을 `batch_write_cells.py`의 `--cells` 인수로 전달한다.

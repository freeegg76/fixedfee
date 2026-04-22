"""
Instruction 탭 파싱 → 변수 매핑 테이블 생성 + 플레이스홀더 탐색.

변수 유형:
  simple  : 정확히 '탭명![컬럼명]' 형식 → 스크립트로 값 조회
  complex : 자연어 설명, 수식, 다중 참조, 날짜 계산 등 → LLM이 계산

사용법:
  # Instruction 탭 JSON으로 매핑 테이블 생성
  python build_mapping.py --instruction-json '{"tab":"Instruction","rows":[...]}'

  # 복제된 탭 셀 값에서 플레이스홀더 [변수명] 탐색
  python build_mapping.py --find-placeholders --cells-json '{"tab":"2025.03","rows":[...]}'
"""

import argparse
import json
import re
import sys

# 정확히 '탭명![컬럼명]' 형식만 simple (+ 없음, 다중 참조 없음)
_SIMPLE_PATTERN = re.compile(r'^[\w가-힣]+!\[[\w가-힣 ]+\]$')


def classify(data_ref: str) -> str:
    """'simple' 또는 'complex' 반환."""
    ref = data_ref.strip()
    if _SIMPLE_PATTERN.match(ref) and "+" not in ref:
        return "simple"
    return "complex"


def col_index_to_letter(index: int) -> str:
    """0-based 열 인덱스 → 컬럼 문자 (0→A, 25→Z, 26→AA)."""
    result = ""
    index += 1
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result


def build_mapping(rows: list[list]) -> dict:
    """
    Instruction 탭 rows → 변수 매핑 딕셔너리.

    반환 형식:
    {
      "변수명": {
        "type": "simple",
        "source_tab": "Client",
        "source_col": "회사명"
      },
      "변수명2": {
        "type": "complex",
        "description": "인보이스가 청구되는 서비스 월로 YYYY/MM으로 표현",
        "example": "2026/04"
      }
    }
    """
    if not rows:
        return {}

    header = rows[0]
    try:
        var_idx = header.index("변수")
        data_idx = header.index("데이터")
    except ValueError as e:
        print(json.dumps({"error": f"Instruction 탭 헤더에서 컬럼을 찾을 수 없음: {e}"}))
        sys.exit(1)

    ex_idx = header.index("예시") if "예시" in header else None

    mapping = {}
    for row in rows[1:]:
        if len(row) <= max(var_idx, data_idx):
            continue

        var_name = row[var_idx].strip()
        data_ref = row[data_idx].strip()

        if not var_name or not data_ref:
            continue

        example = row[ex_idx].strip() if ex_idx is not None and len(row) > ex_idx else ""
        kind = classify(data_ref)

        if kind == "simple":
            tab, col = data_ref.split("!", 1)
            # 컬럼명에서 [] 제거
            col_clean = col.strip().lstrip("[").rstrip("]")
            mapping[var_name] = {
                "type": "simple",
                "source_tab": tab.strip(),
                "source_col": col_clean,
            }
        else:
            mapping[var_name] = {
                "type": "complex",
                "description": data_ref,
                "example": example,
            }

    return {"mapping": mapping}


def find_placeholders(rows: list[list], formula_rows: list[list] | None = None) -> dict:
    """
    2D 셀 값에서 [변수명] 패턴을 탐색.
    반환: {"A1": "[회사명]", "B5": "[청구총액]", ...}

    formula_rows: read_sheets.py --formula 로 읽은 수식 원문 2D 배열.
                  제공 시 수식 셀(=로 시작)은 플레이스홀더 대상에서 제외.

    한글 범위 정규식 대신 '[' ... ']' 구조로 매칭 (Windows 인코딩 환경 호환).
    단, 빈 대괄호 [] 와 셀 수식 등은 제외하기 위해 최소 2자 이상 요구.
    """
    pattern = re.compile(r"(\[[^\[\]]{2,}\])")
    found = {}

    for r_idx, row in enumerate(rows):
        for c_idx, cell in enumerate(row):
            match = pattern.search(str(cell))
            if not match:
                continue

            # 수식 셀이면 제외 (formula_rows 제공 시)
            if formula_rows is not None:
                try:
                    formula_cell = str(formula_rows[r_idx][c_idx])
                    if formula_cell.startswith("="):
                        continue
                except IndexError:
                    pass

            col_letter = col_index_to_letter(c_idx)
            cell_addr = f"{col_letter}{r_idx + 1}"
            found[cell_addr] = match.group(1)

    return {"placeholders": found}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--instruction-json", default=None,
                        help="read_sheets.py 출력 JSON 문자열 (Instruction 탭)")
    parser.add_argument("--find-placeholders", action="store_true",
                        help="플레이스홀더 탐색 모드")
    parser.add_argument("--cells-json", default=None,
                        help="read_sheets.py 출력 JSON 문자열 (복제된 탭, 표시값)")
    parser.add_argument("--cells-file", default=None,
                        help="--cells-json 대신 파일 경로로 전달")
    parser.add_argument("--formula-json", default=None,
                        help="read_sheets.py --formula 출력 JSON 문자열 (수식 셀 제외용)")
    parser.add_argument("--formula-file", default=None,
                        help="--formula-json 대신 파일 경로로 전달")
    args = parser.parse_args()

    if args.find_placeholders:
        # cells 읽기 (JSON 문자열 또는 파일)
        if args.cells_file:
            with open(args.cells_file, encoding="utf-8") as f:
                data = json.load(f)
        elif args.cells_json:
            data = json.loads(args.cells_json)
        else:
            print(json.dumps({"error": "--cells-json 또는 --cells-file 필요"}))
            sys.exit(1)
        rows = data.get("rows", [])

        # formula 읽기 (선택)
        formula_rows = None
        if args.formula_file:
            with open(args.formula_file, encoding="utf-8") as f:
                formula_rows = json.load(f).get("rows", [])
        elif args.formula_json:
            formula_rows = json.loads(args.formula_json).get("rows", [])

        result = find_placeholders(rows, formula_rows)
        print(json.dumps(result, ensure_ascii=False))
        return

    if not args.instruction_json:
        print(json.dumps({"error": "--instruction-json 필요"}))
        sys.exit(1)

    data = json.loads(args.instruction_json)
    rows = data.get("rows", [])
    result = build_mapping(rows)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()

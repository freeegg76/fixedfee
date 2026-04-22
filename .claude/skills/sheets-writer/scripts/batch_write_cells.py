"""
새로 생성된 탭의 셀에 값을 일괄 입력.

사용법:
  python batch_write_cells.py \
    --spreadsheet-id TARGET_ID \
    --tab-name "2025.03" \
    --cells '{"B3": "삼성전자", "C5": "1000000"}'

  # 숫자 포맷 적용 (금액 셀)
  python batch_write_cells.py \
    --spreadsheet-id TARGET_ID \
    --tab-name "2025.03" \
    --sheet-id 12345 \
    --cells '{"G20": "3500000"}' \
    --user-entered \
    --format-cells "G20,H22,H23,H25" \
    --currency KRW

환경변수:
  GOOGLE_SERVICE_ACCOUNT_KEY: Service Account JSON 키파일 경로
"""

import argparse
import json
import os
import re
import sys

from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def get_service():
    key_path = os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY")
    if not key_path:
        print(json.dumps({"error": "GOOGLE_SERVICE_ACCOUNT_KEY 환경변수가 설정되지 않았습니다."}))
        sys.exit(1)
    creds = service_account.Credentials.from_service_account_file(key_path, scopes=SCOPES)
    return build("sheets", "v4", credentials=creds)


def cell_addr_to_indices(addr: str) -> tuple[int, int]:
    """'G20' → (row_index, col_index) 0-based."""
    match = re.match(r"([A-Za-z]+)(\d+)", addr)
    if not match:
        raise ValueError(f"Invalid cell address: {addr}")
    col_str, row_str = match.group(1).upper(), match.group(2)
    col_idx = 0
    for ch in col_str:
        col_idx = col_idx * 26 + (ord(ch) - ord("A") + 1)
    col_idx -= 1
    row_idx = int(row_str) - 1
    return row_idx, col_idx


def apply_number_format(service, spreadsheet_id: str, sheet_id: int,
                        cell_addrs: list[str], currency: str) -> None:
    """
    지정 셀에 통화 숫자 포맷 적용.
    KRW: ₩#,##0 (소수점 없음)
    USD: $#,##0.00 (소수점 2자리)
    """
    if currency == "KRW":
        pattern = "₩#,##0"
    elif currency == "USD":
        pattern = "$#,##0.00"
    else:
        pattern = "#,##0"

    requests = []
    for addr in cell_addrs:
        row_idx, col_idx = cell_addr_to_indices(addr.strip())
        requests.append({
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": row_idx,
                    "endRowIndex": row_idx + 1,
                    "startColumnIndex": col_idx,
                    "endColumnIndex": col_idx + 1,
                },
                "cell": {
                    "userEnteredFormat": {
                        "numberFormat": {
                            "type": "CURRENCY",
                            "pattern": pattern,
                        }
                    }
                },
                "fields": "userEnteredFormat.numberFormat",
            }
        })

    if requests:
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": requests},
        ).execute()


def batch_write(service, spreadsheet_id: str, tab_name: str, cells: dict[str, str],
                user_entered: bool = False) -> int:
    """
    cells: {"A1": "value", "B5": "=SUM(A1:A5)", ...}
    user_entered=True 이면 수식·날짜 등 Google Sheets가 해석하도록 USER_ENTERED 사용.
    반환: 업데이트된 셀 수
    """
    input_option = "USER_ENTERED" if user_entered else "RAW"
    data = [
        {
            "range": f"'{tab_name}'!{addr}",
            "values": [[value]],
        }
        for addr, value in cells.items()
    ]
    result = (
        service.spreadsheets()
        .values()
        .batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={
                "valueInputOption": input_option,
                "data": data,
            },
        )
        .execute()
    )
    return result.get("totalUpdatedCells", len(cells))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--spreadsheet-id", required=True)
    parser.add_argument("--tab-name", required=True)
    parser.add_argument("--cells", required=True, help='JSON 문자열 {"셀주소": "값", ...}')
    parser.add_argument("--user-entered", action="store_true",
                        help="수식 복원 시 사용. Google Sheets가 값을 해석하도록 USER_ENTERED 모드 사용")
    parser.add_argument("--sheet-id", type=int, default=None,
                        help="숫자 포맷 적용 시 필요한 sheetId (정수)")
    parser.add_argument("--format-cells", default=None,
                        help="숫자 포맷을 적용할 셀 주소 목록 (쉼표 구분, 예: G20,H22,H23,H25)")
    parser.add_argument("--currency", default=None,
                        help="통화 코드 (KRW 또는 USD). --format-cells와 함께 사용")
    args = parser.parse_args()

    try:
        cells = json.loads(args.cells)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"--cells JSON 파싱 실패: {e}"}))
        sys.exit(1)

    service = get_service()
    updated = batch_write(service, args.spreadsheet_id, args.tab_name, cells,
                          user_entered=args.user_entered)

    if args.format_cells and args.currency and args.sheet_id is not None:
        fmt_cells = [c.strip() for c in args.format_cells.split(",") if c.strip()]
        apply_number_format(service, args.spreadsheet_id, args.sheet_id, fmt_cells, args.currency)

    print(json.dumps({"updated_cells": updated}))


if __name__ == "__main__":
    main()

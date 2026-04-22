"""
Google Sheets 탭 데이터 읽기 스크립트.

사용법:
  # 값만 읽기
  python read_sheets.py --spreadsheet-id SHEET_ID --tab "Client"

  # 탭 목록 조회 (중복 확인용)
  python read_sheets.py --spreadsheet-id SHEET_ID --list-tabs

  # Template sheetId 조회
  python read_sheets.py --spreadsheet-id SHEET_ID --get-sheet-id --tab "Template"

환경변수:
  GOOGLE_SERVICE_ACCOUNT_KEY: Service Account JSON 키파일 경로
"""

import argparse
import json
import os
import sys

from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def get_service():
    key_path = os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY")
    if not key_path:
        print(json.dumps({"error": "GOOGLE_SERVICE_ACCOUNT_KEY 환경변수가 설정되지 않았습니다."}))
        sys.exit(1)
    creds = service_account.Credentials.from_service_account_file(key_path, scopes=SCOPES)
    return build("sheets", "v4", credentials=creds)


def read_values(service, spreadsheet_id: str, tab: str, formula_mode: bool = False) -> list[list]:
    """탭 전체 값을 2D 리스트로 반환.
    formula_mode=True 이면 수식을 그대로 반환 (FORMULA render option).
    """
    render = "FORMULA" if formula_mode else "FORMATTED_VALUE"
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=tab, valueRenderOption=render)
        .execute()
    )
    return result.get("values", [])


def list_tabs(service, spreadsheet_id: str) -> list[dict]:
    """탭 이름과 sheetId 목록 반환."""
    result = (
        service.spreadsheets()
        .get(spreadsheetId=spreadsheet_id, fields="sheets.properties")
        .execute()
    )
    return [
        {"title": s["properties"]["title"], "sheetId": s["properties"]["sheetId"]}
        for s in result.get("sheets", [])
    ]


def get_sheet_id(service, spreadsheet_id: str, tab: str) -> int | None:
    """특정 탭 이름의 sheetId 반환. 없으면 None."""
    tabs = list_tabs(service, spreadsheet_id)
    for t in tabs:
        if t["title"] == tab:
            return t["sheetId"]
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--spreadsheet-id", required=True)
    parser.add_argument("--tab", default=None)
    parser.add_argument("--list-tabs", action="store_true")
    parser.add_argument("--get-sheet-id", action="store_true")
    parser.add_argument("--formula", action="store_true", help="수식 원문 반환 (수식 셀 감지용)")
    args = parser.parse_args()

    service = get_service()

    if args.list_tabs:
        tabs = list_tabs(service, args.spreadsheet_id)
        print(json.dumps({"tabs": tabs}, ensure_ascii=False))
        return

    if not args.tab:
        print(json.dumps({"error": "--tab 인수가 필요합니다."}))
        sys.exit(1)

    if args.get_sheet_id:
        sheet_id = get_sheet_id(service, args.spreadsheet_id, args.tab)
        if sheet_id is None:
            print(json.dumps({"error": f"탭을 찾을 수 없음: {args.tab}"}))
            sys.exit(1)
        print(json.dumps({"sheet_id": sheet_id}))
        return

    rows = read_values(service, args.spreadsheet_id, args.tab, formula_mode=args.formula)
    print(json.dumps({"tab": args.tab, "rows": rows, "formula_mode": args.formula}, ensure_ascii=False))


if __name__ == "__main__":
    main()

"""
마스터 스프레드시트의 Template 탭을 고객사 Sheets에 복제하고 탭 이름을 변경.

사용법:
  python copy_template_tab.py \
    --master-sheet-id MASTER_ID \
    --target-sheet-id TARGET_ID \
    --tab-name "2025.03" \
    --template-sheet-id 123456

환경변수:
  GOOGLE_SERVICE_ACCOUNT_KEY: Service Account JSON 키파일 경로
"""

import argparse
import json
import os
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


def copy_template(service, master_sheet_id: str, template_sheet_id: int, target_sheet_id: str) -> int:
    """Template 탭을 target spreadsheet에 복사. 새 sheetId 반환."""
    result = (
        service.spreadsheets()
        .sheets()
        .copyTo(
            spreadsheetId=master_sheet_id,
            sheetId=template_sheet_id,
            body={"destinationSpreadsheetId": target_sheet_id},
        )
        .execute()
    )
    return result["sheetId"]


def rename_tab(service, spreadsheet_id: str, sheet_id: int, new_title: str):
    """탭 이름 변경."""
    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "requests": [
                {
                    "updateSheetProperties": {
                        "properties": {"sheetId": sheet_id, "title": new_title},
                        "fields": "title",
                    }
                }
            ]
        },
    ).execute()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--master-sheet-id", required=True, help="마스터 스프레드시트 ID")
    parser.add_argument("--target-sheet-id", required=True, help="고객사 스프레드시트 ID")
    parser.add_argument("--tab-name", required=True, help="새 탭 이름 (예: 2025.03)")
    parser.add_argument("--template-sheet-id", required=True, type=int, help="Template 탭 sheetId (정수)")
    args = parser.parse_args()

    service = get_service()

    new_sheet_id = copy_template(
        service, args.master_sheet_id, args.template_sheet_id, args.target_sheet_id
    )
    rename_tab(service, args.target_sheet_id, new_sheet_id, args.tab_name)

    sheet_url = (
        f"https://docs.google.com/spreadsheets/d/{args.target_sheet_id}"
        f"/edit#gid={new_sheet_id}"
    )
    print(json.dumps({"new_sheet_id": new_sheet_id, "sheet_url": sheet_url}))


if __name__ == "__main__":
    main()

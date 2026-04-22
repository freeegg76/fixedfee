"""
Google Sheets 탭을 PDF로 내보내는 스크립트.
서비스 계정 인증으로 특정 탭(sheetId 정수)을 PDF 파일로 저장한다.

사용법:
  python export_pdf.py \
    --spreadsheet-id {KEY} \
    --sheet-id {new_sheet_id} \
    --output "output/Dongkook Fixed Fee Invoice 202605.pdf"

환경변수:
  GOOGLE_SERVICE_ACCOUNT_KEY: Service Account JSON 키파일 경로 (필수)
"""

import argparse
import json
import os
import sys

import google.auth.transport.requests
from google.oauth2 import service_account


SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly",
          "https://www.googleapis.com/auth/drive.readonly"]


def export_pdf(spreadsheet_id: str, sheet_id: int, output_path: str):
    key_path = os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY")
    if not key_path:
        raise Exception("GOOGLE_SERVICE_ACCOUNT_KEY 환경변수가 설정되지 않았습니다")

    creds = service_account.Credentials.from_service_account_file(key_path, scopes=SCOPES)
    authed_session = google.auth.transport.requests.AuthorizedSession(creds)

    url = (
        f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export"
        f"?format=pdf"
        f"&gid={sheet_id}"
        f"&portrait=true"
        f"&size=A4"
        f"&fitw=true"
        f"&sheetnames=false"
        f"&printtitle=false"
        f"&pagenumbers=false"
        f"&gridlines=false"
        f"&fzr=false"
    )

    response = authed_session.get(url)
    if response.status_code != 200:
        raise Exception(f"PDF 내보내기 실패: HTTP {response.status_code} — {response.text[:200]}")

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(response.content)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--spreadsheet-id", required=True)
    parser.add_argument("--sheet-id", required=True, type=int, help="탭의 sheetId (정수)")
    parser.add_argument("--output", required=True, help="저장할 PDF 파일 경로")
    args = parser.parse_args()

    try:
        export_pdf(args.spreadsheet_id, args.sheet_id, args.output)
        print(json.dumps({"status": "success", "output": args.output}))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()

"""
Gmail API (OAuth 2.0)로 메일 초안을 저장하는 스크립트.

사용법:
  python create_draft.py \
    --to "to1@example.com,to2@example.com" \
    --cc "cc1@example.com" \
    --subject "[아마존_Invoice] CompanyA Fixed Fee invoice 202604" \
    --body "안녕하세요..." \
    --attachment "output/Dongkook Fixed Fee Invoice 202605.pdf"

첫 실행 시 브라우저가 열려 Google 계정 승인을 요청합니다.
이후 실행은 저장된 토큰(gmail_token.json)을 자동 사용합니다.

환경변수:
  GMAIL_FROM: 발신자 표시 주소 (기본값: info@forsit.co.kr)
  GMAIL_CC_ALWAYS: 모든 초안에 강제 추가할 CC (기본값: info@forsit.co.kr)
  OAUTH_CLIENT_SECRET: OAuth 클라이언트 시크릿 파일 경로
                       (기본값: c:/Dev/Fixed Fee/oauth_client_secret.json)
"""

import argparse
import base64
import json
import os
import sys
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]
TOKEN_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "gmail_token.json")
TOKEN_PATH = os.path.normpath(TOKEN_PATH)


def get_credentials(client_secret_path: str) -> Credentials:
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
    return creds


def create_draft(to_addr: str, cc_addr: str, subject: str, body: str,
                 from_addr: str, creds: Credentials, attachment_path: str = None):
    # 항상 추가할 CC 주소 병합
    always_cc = os.environ.get("GMAIL_CC_ALWAYS", "info@forsit.co.kr")
    cc_parts = [a.strip() for a in cc_addr.split(",") if a.strip()]
    if always_cc and always_cc not in cc_parts:
        cc_parts.append(always_cc)
    final_cc = ",".join(cc_parts)

    msg = MIMEMultipart()
    msg["From"] = from_addr
    msg["To"] = to_addr
    if final_cc:
        msg["Cc"] = final_cc
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    if attachment_path:
        if not os.path.exists(attachment_path):
            raise Exception(f"첨부파일을 찾을 수 없습니다: {attachment_path}")
        filename = os.path.basename(attachment_path)
        with open(attachment_path, "rb") as f:
            part = MIMEApplication(f.read(), _subtype="pdf")
        part.add_header("Content-Disposition", "attachment", filename=filename)
        msg.attach(part)

    service = build("gmail", "v1", credentials=creds)
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    draft_body = {"message": {"raw": raw}}
    service.users().drafts().create(userId="me", body=draft_body).execute()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--to", required=True)
    parser.add_argument("--cc", default="")
    parser.add_argument("--subject", required=True)
    parser.add_argument("--body", required=True)
    parser.add_argument("--attachment", default=None)
    args = parser.parse_args()

    from_addr = os.environ.get("GMAIL_FROM", "info@forsit.co.kr")
    client_secret_path = os.environ.get(
        "OAUTH_CLIENT_SECRET",
        "c:/Dev/Fixed Fee/client_secret_600358750353-kqebejvfpp93u03ckl5rsnf7jkbmh6qs.apps.googleusercontent.com.json"
    )

    if not os.path.exists(client_secret_path):
        print(json.dumps({"error": f"OAuth 클라이언트 시크릿 파일 없음: {client_secret_path}"}))
        sys.exit(1)

    try:
        creds = get_credentials(client_secret_path)
        create_draft(
            to_addr=args.to,
            cc_addr=args.cc,
            subject=args.subject,
            body=args.body,
            from_addr=from_addr,
            creds=creds,
            attachment_path=args.attachment,
        )
        print(json.dumps({"status": "success", "subject": args.subject}))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()

"""
Gmail OAuth 2.0 토큰 최초 발급 스크립트.
한 번만 실행하면 gmail_token.json이 생성되고,
이후 create_draft.py는 토큰을 자동으로 재사용합니다.
"""

import os
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]
CLIENT_SECRET = "c:/Dev/Fixed Fee/client_secret_600358750353-kqebejvfpp93u03ckl5rsnf7jkbmh6qs.apps.googleusercontent.com.json"
TOKEN_PATH = "c:/Dev/Fixed Fee/gmail_token.json"

flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, SCOPES)
# 브라우저 자동 열기 없이 URL만 출력 → info@forsit.co.kr만 로그인된 창에 붙여넣기
creds = flow.run_local_server(port=0, open_browser=False, login_hint="info@forsit.co.kr")

with open(TOKEN_PATH, "w") as f:
    f.write(creds.to_json())

print(f"토큰 저장 완료: {TOKEN_PATH}")

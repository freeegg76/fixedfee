import os, json
from google.oauth2 import service_account
from googleapiclient.discovery import build

key_path = os.environ["GOOGLE_SERVICE_ACCOUNT_KEY"]
creds = service_account.Credentials.from_service_account_file(
    key_path, scopes=["https://www.googleapis.com/auth/spreadsheets"])
service = build("sheets", "v4", credentials=creds)

spreadsheet_id = "19QreH2ko4-MJxSAIlfDWQb0D7CY_vZPOjosjKVSnWXA"
sheet_id = 1226136081

body = {"requests": [{"deleteSheet": {"sheetId": sheet_id}}]}
service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
print(json.dumps({"deleted": True, "sheetId": sheet_id}))

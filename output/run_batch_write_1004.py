import subprocess
import json
import sys

cells = {
  "C6": "주식회사 제네웰",
  "C7": "경기도 성남시 중원구 사기막골로62번길 37(상대원동, 스타타워 6층)",
  "C8": "206-81-28319",
  "C9": "한상덕",
  "C12": "2026/05",
  "C13": "Genewel-202605-Fixed-01",
  "C14": "2026/05/01",
  "C15": "2026/05/15",
  "B20": "2026/05-Service Fee",
  "D20": "2026/05/01 ~ 2026/05/31",
  "G20": 4500000,
  "E22": "KRW",
  "H23": 450000,
  "H25": 4950000
}

cells_json = json.dumps(cells, ensure_ascii=False)

import sys
sys.path.insert(0, "C:/Dev/Fixed Fee/.claude/skills/sheets-writer/scripts")

import importlib.util, types, os

os.environ["GOOGLE_SERVICE_ACCOUNT_KEY"] = "c:/Dev/Fixed Fee/credentials.json"

spec = importlib.util.spec_from_file_location("batch_write_cells", "C:/Dev/Fixed Fee/.claude/skills/sheets-writer/scripts/batch_write_cells.py")
mod = importlib.util.load_from_spec(spec) if hasattr(importlib.util, 'load_from_spec') else None

# Use direct import approach
from googleapiclient.discovery import build
from google.oauth2 import service_account

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
key_path = "c:/Dev/Fixed Fee/credentials.json"
creds = service_account.Credentials.from_service_account_file(key_path, scopes=SCOPES)
service = build("sheets", "v4", credentials=creds)

spreadsheet_id = "1iAG1hYLdLXq8eLkVEdtbPLkBVuWIxCqjT4exZT7rEA8"
tab_name = "2026.05"

# Write cells
data = [
    {"range": f"'{tab_name}'!{addr}", "values": [[value]]}
    for addr, value in cells.items()
]
result = service.spreadsheets().values().batchUpdate(
    spreadsheetId=spreadsheet_id,
    body={"valueInputOption": "USER_ENTERED", "data": data}
).execute()
print(json.dumps({"updated_cells": result.get("totalUpdatedCells", len(cells))}))

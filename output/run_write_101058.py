"""Helper script to write cells from a JSON file to a Google Sheet."""
import json
import os
import sys

# Add the project root to the path
sys.path.insert(0, r"c:\Dev\Fixed Fee")

# Import from the sheets-writer skill
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def get_service():
    key_path = os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY")
    creds = service_account.Credentials.from_service_account_file(key_path, scopes=SCOPES)
    return build("sheets", "v4", credentials=creds)

def cell_addr_to_indices(addr):
    import re
    match = re.match(r"([A-Za-z]+)(\d+)", addr)
    col_str, row_str = match.group(1).upper(), match.group(2)
    col_idx = 0
    for ch in col_str:
        col_idx = col_idx * 26 + (ord(ch) - ord("A") + 1)
    col_idx -= 1
    row_idx = int(row_str) - 1
    return row_idx, col_idx

spreadsheet_id = "1qtfvZ-ImX-WqSzhj2AdFrEWOuRXBOKa5dV1JtuvzF9c"
tab_name = "2026.06"
new_sheet_id = 183831214
currency = "KRW"

cells = {
    "C6": "주식회사 바임",
    "C7": "대전광역시 유성구 테크노1로 30 (관평동)",
    "C8": "757-87-01595",
    "C9": "박종현, 전동훈",
    "C12": "2026/06",
    "I12": "064-177713-04-036",
    "C13": "Vaim-202606-Fixed-01",
    "C14": "2026/06/01",
    "C15": "2026/06/15",
    "B20": "2026/06-Service Fee",
    "D20": "2026/06/01 ~ 2026/06/30",
    "G20": 3500000,
    "E22": "KRW",
    "H23": 350000,
    "H25": 3850000,
    "I14": ""
}

service = get_service()

# Write cells
data = [
    {
        "range": f"'{tab_name}'!{addr}",
        "values": [[value]],
    }
    for addr, value in cells.items()
]
result = service.spreadsheets().values().batchUpdate(
    spreadsheetId=spreadsheet_id,
    body={
        "valueInputOption": "USER_ENTERED",
        "data": data,
    },
).execute()
print(f"Write result: updated {result.get('totalUpdatedCells', 0)} cells")

# Apply number format to money cells
# G20=[서비스 공급가액], H23=[부가가치세액], H25=[청구총액], H22 (formula =G20), C16 (formula =H25)
format_cells = ["G20", "H23", "H25", "H22", "C16"]
pattern = "₩#,##0"  # KRW

requests = []
for addr in format_cells:
    row_idx, col_idx = cell_addr_to_indices(addr)
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": new_sheet_id,
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

service.spreadsheets().batchUpdate(
    spreadsheetId=spreadsheet_id,
    body={"requests": requests},
).execute()
print("Number format applied to money cells")
print(json.dumps({"status": "success"}))

import json, os, sys

os.environ["PYTHONUTF8"] = "1"
os.environ["GOOGLE_SERVICE_ACCOUNT_KEY"] = "c:/Dev/Fixed Fee/credentials.json"

# Add skills path
sys.path.insert(0, r"C:\Dev\Fixed Fee")

from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
key_path = os.environ["GOOGLE_SERVICE_ACCOUNT_KEY"]
creds = service_account.Credentials.from_service_account_file(key_path, scopes=SCOPES)
service = build("sheets", "v4", credentials=creds)

spreadsheet_id = "1GdagWo40DxaWilfeMeGF_7flibtSpvnO371EmVPFgS8"
tab_name = "2026.06"
new_sheet_id = 1827260056

cells = {
    "C6": "동국제약 주식회사",
    "C7": "서울특별시 강남구 영동대로 715",
    "C8": "301-85-08241",
    "C9": "송준호",
    "C12": "2026/06",
    "I12": "064-177713-04-036",
    "C13": "Dongkook-202606-Fixed-01",
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

# Save the cells JSON for reference
with open(r"c:\Dev\Fixed Fee\output\cells_write_000102_acct.json", "w", encoding="utf-8") as f:
    json.dump(cells, f, ensure_ascii=False)

# Build batch update data
import re

def col_letters_to_index(col_str):
    idx = 0
    for ch in col_str.upper():
        idx = idx * 26 + (ord(ch) - ord('A') + 1)
    return idx - 1

def cell_addr_to_indices(addr):
    match = re.match(r"([A-Za-z]+)(\d+)", addr)
    col_str, row_str = match.group(1).upper(), match.group(2)
    row_idx = int(row_str) - 1
    col_idx = col_letters_to_index(col_str)
    return row_idx, col_idx

data = []
for addr, val in cells.items():
    r, c = cell_addr_to_indices(addr)
    data.append({
        "range": f"'{tab_name}'!{addr}",
        "values": [[val]]
    })

body = {
    "valueInputOption": "USER_ENTERED",
    "data": data
}

result = service.spreadsheets().values().batchUpdate(
    spreadsheetId=spreadsheet_id,
    body=body
).execute()

print(json.dumps({"updated_cells": result.get("totalUpdatedCells", len(cells))}))

# Now apply number format
import re

def col_letters_to_index2(col_str):
    idx = 0
    for ch in col_str.upper():
        idx = idx * 26 + (ord(ch) - ord('A') + 1)
    return idx - 1

def cell_addr_to_grid(addr, sheet_id):
    match = re.match(r"([A-Za-z]+)(\d+)", addr)
    col_str, row_str = match.group(1).upper(), match.group(2)
    row_idx = int(row_str) - 1
    col_idx = col_letters_to_index2(col_str)
    return {
        "sheetId": sheet_id,
        "startRowIndex": row_idx,
        "endRowIndex": row_idx + 1,
        "startColumnIndex": col_idx,
        "endColumnIndex": col_idx + 1
    }

# KRW format cells: G20(서비스공급가액), H23(부가가치세액), H25(청구총액), H22(=G20 formula), C16(=H25 formula)
currency = "KRW"
format_pattern = "₩#,##0" if currency == "KRW" else "$#,##0.00"
format_cells = ["G20", "H23", "H25", "H22", "C16"]

requests = []
for addr in format_cells:
    grid = cell_addr_to_grid(addr, new_sheet_id)
    requests.append({
        "repeatCell": {
            "range": grid,
            "cell": {
                "userEnteredFormat": {
                    "numberFormat": {
                        "type": "CURRENCY",
                        "pattern": format_pattern
                    }
                }
            },
            "fields": "userEnteredFormat.numberFormat"
        }
    })

fmt_result = service.spreadsheets().batchUpdate(
    spreadsheetId=spreadsheet_id,
    body={"requests": requests}
).execute()

print(json.dumps({"format_applied": len(requests)}))

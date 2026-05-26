import json
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
import re

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
key_path = "c:/Dev/Fixed Fee/credentials.json"
creds = service_account.Credentials.from_service_account_file(key_path, scopes=SCOPES)
service = build("sheets", "v4", credentials=creds)

spreadsheet_id = "1iAG1hYLdLXq8eLkVEdtbPLkBVuWIxCqjT4exZT7rEA8"
sheet_id = 291936369
currency = "KRW"
format_cells = ["G20", "H22", "H23", "H25"]

pattern = "₩#,##0"

def cell_addr_to_indices(addr):
    match = re.match(r"([A-Za-z]+)(\d+)", addr)
    col_str, row_str = match.group(1).upper(), match.group(2)
    col_idx = 0
    for ch in col_str:
        col_idx = col_idx * 26 + (ord(ch) - ord("A") + 1)
    col_idx -= 1
    row_idx = int(row_str) - 1
    return row_idx, col_idx

requests = []
for addr in format_cells:
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

result = service.spreadsheets().batchUpdate(
    spreadsheetId=spreadsheet_id,
    body={"requests": requests},
).execute()

print(json.dumps({"format_applied": True, "cells": format_cells}))

import subprocess
import sys
import json

cells = {
    "C6": "동화약품(주)",
    "C7": "서울특별시 중구 남대문로 9길 25, 6층~8층(다동)",
    "C8": "110-81-00102",
    "C9": "유준하",
    "C12": "2026/05",
    "C13": "Dongwha-202605-Fixed-01",
    "C14": "2026/05/01",
    "C15": "2026/05/15",
    "B20": "2026/05-Service Fee",
    "D20": "2026/05/01 ~ 2026/05/31",
    "G20": 3500000,
    "E22": "KRW",
    "H23": 350000,
    "H25": 3850000
}

cells_json = json.dumps(cells, ensure_ascii=False)

import os, sys
sys.path.insert(0, r"C:\Dev\Fixed Fee\.claude\skills\sheets-writer\scripts")

# Import the module directly
import importlib.util
spec = importlib.util.spec_from_file_location("batch_write_cells", r"C:\Dev\Fixed Fee\.claude\skills\sheets-writer\scripts\batch_write_cells.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
key_path = os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY")
creds = service_account.Credentials.from_service_account_file(key_path, scopes=SCOPES)
service = build("sheets", "v4", credentials=creds)

spreadsheet_id = "1W6Eno78tt3DSVZ8d5lhMqjxSg1mICufooAmlCPVZh28"
tab_name = "2026.05"
new_sheet_id = 2003528255

# Write values
updated = mod.batch_write(service, spreadsheet_id, tab_name, cells, user_entered=True)
print(f"Updated cells: {updated}")

# Apply number format to monetary cells + H22
fmt_cells = ["G20", "H22", "H23", "H25"]
mod.apply_number_format(service, spreadsheet_id, new_sheet_id, fmt_cells, "KRW")
print("Number format applied to: " + ", ".join(fmt_cells))

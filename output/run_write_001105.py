import json, os, sys
sys.path.insert(0, r"c:\Dev\Fixed Fee\.claude\skills\sheets-writer\scripts")
os.environ["GOOGLE_SERVICE_ACCOUNT_KEY"] = "c:/Dev/Fixed Fee/credentials.json"

from batch_write_cells import get_service, batch_write, apply_number_format

spreadsheet_id = "1tPR4Tr-_jYCDWLEyDGHCe3_nZv83JWG871zqTd3MgD8"
tab_name = "2026.06"
new_sheet_id = 1400000331
currency = "KRW"

cells = {
    "C6": "주식회사 올그레이스",
    "C7": "서울특별시 강남구 학동로17길 4-5, 3층(논현동)",
    "C8": "623-81-03231",
    "C9": "김강일",
    "C12": "2026/06",
    "I12": "064-177713-04-036",
    "C13": "Seleve-202606-Fixed-01",
    "C14": "2026/06/01",
    "C15": "2026/06/15",
    "B20": "2026/06-Service Fee",
    "D20": "2026/06/01 ~ 2026/06/30",
    "G20": 3500000,
    "E22": "KRW",
    "H23": 350000,
    "H25": 3850000,
    "I14": "",
}

service = get_service()
updated = batch_write(service, spreadsheet_id, tab_name, cells, user_entered=True)
print(f"Updated cells: {updated}")

# Apply number format to amount cells + H22 + C16
format_cells = ["G20", "H23", "H25", "H22", "C16"]
apply_number_format(service, spreadsheet_id, new_sheet_id, format_cells, currency)
print("Number format applied")
print(json.dumps({"status": "success", "updated_cells": updated}))

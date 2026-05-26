"""Helper to run batch_write_cells using cells from a JSON file."""
import json
import sys
import os

sys.path.insert(0, r"c:\Dev\Fixed Fee\.claude\skills\sheets-writer\scripts")
from batch_write_cells import get_service, batch_write, apply_number_format

SPREADSHEET_ID = "1p4ubem11TaweSuPjgBy5CN3xC2uvaZBL7xZDLh6WFww"
TAB_NAME = "2026.06"
NEW_SHEET_ID = 454584524
CURRENCY = "KRW"
CELLS_FILE = r"c:\Dev\Fixed Fee\output\cells_write_000634.json"

with open(CELLS_FILE, encoding="utf-8") as f:
    cells = json.load(f)

service = get_service()
updated = batch_write(service, SPREADSHEET_ID, TAB_NAME, cells, user_entered=True)
print(json.dumps({"updated_cells": updated}))

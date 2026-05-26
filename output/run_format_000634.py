"""Helper to apply number format to amount cells."""
import json
import sys

sys.path.insert(0, r"c:\Dev\Fixed Fee\.claude\skills\sheets-writer\scripts")
from batch_write_cells import get_service, apply_number_format

SPREADSHEET_ID = "1p4ubem11TaweSuPjgBy5CN3xC2uvaZBL7xZDLh6WFww"
NEW_SHEET_ID = 454584524
CURRENCY = "KRW"
FORMAT_CELLS = ["G20", "H23", "H25", "H22", "C16"]

service = get_service()
apply_number_format(service, SPREADSHEET_ID, NEW_SHEET_ID, FORMAT_CELLS, CURRENCY)
print(json.dumps({"formatted_cells": FORMAT_CELLS, "currency": CURRENCY}))

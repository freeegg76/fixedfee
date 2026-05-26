import json
import importlib.util, sys

spec = importlib.util.spec_from_file_location(
    "batch_write_cells",
    r"c:\Dev\Fixed Fee\.claude\skills\sheets-writer\scripts\batch_write_cells.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

service = mod.get_service()
spreadsheet_id = "11j-9lp0yv8eecvupffmieLmuczoktooYahyDhikVsfM"
sheet_id = 1357144682
currency = "KRW"
format_cells = ["G20", "H22", "H23", "H25", "C16"]

mod.apply_number_format(service, spreadsheet_id, sheet_id, format_cells, currency)
print(json.dumps({"status": "format applied", "cells": format_cells, "currency": currency}))

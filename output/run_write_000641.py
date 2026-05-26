import subprocess, sys, os

cells = {
    "C6": "주식회사 바람인터내셔날",
    "C7": "서울특별시 강남구 도산대로 317, 12층",
    "C8": "234-81-00766",
    "C9": "박래현",
    "C12": "2026/06",
    "I12": "064-177713-04-036",
    "C13": "DearDahlia-202606-Fixed-01",
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

import json
import importlib.util, sys as _sys

# Directly import and call the module
spec = importlib.util.spec_from_file_location(
    "batch_write_cells",
    r"c:\Dev\Fixed Fee\.claude\skills\sheets-writer\scripts\batch_write_cells.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

service = mod.get_service()
updated = mod.batch_write(service, "11j-9lp0yv8eecvupffmieLmuczoktooYahyDhikVsfM", "2026.06", cells, user_entered=True)
print(json.dumps({"updated_cells": updated}))

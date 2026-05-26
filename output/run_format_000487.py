import sys, json

sys.path.insert(0, r"c:\Dev\Fixed Fee\.claude\skills\sheets-writer\scripts")

sys.argv = [
    "batch_write_cells.py",
    "--spreadsheet-id", "1jgz7YRJETdSp6pPi6ASlc35eV0w_fx9GZiWdWiLJtPY",
    "--tab-name", "2026.06",
    "--sheet-id", "596208054",
    "--cells", "{}",
    "--format-cells", "G20,H22,H23,H25,C16",
    "--currency", "KRW"
]

import batch_write_cells
batch_write_cells.main()
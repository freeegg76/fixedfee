import sys, json, os

sys.path.insert(0, r"c:\Dev\Fixed Fee\.claude\skills\sheets-writer\scripts")

cells = {
    "I14": "",
    "D20": "2026/06/01 ~ 2026/06/30",
    "H25": 3850000,
    "C15": "2026/06/15",
    "C8": "134-81-29992",
    "E22": "KRW",
    "H23": 350000,
    "C7": "충청남도 당진시 합덕읍 인더스파크로 170(종근당건강)",
    "G20": 3500000,
    "C12": "2026/06",
    "C6": "종근당건강(주)",
    "C13": "CKD-202606-Fixed-01",
    "C14": "2026/06/01",
    "C9": "정수철",
    "B20": "2026/06-Service Fee",
    "I12": "064-177713-04-036"
}

sys.argv = [
    "batch_write_cells.py",
    "--spreadsheet-id", "1jgz7YRJETdSp6pPi6ASlc35eV0w_fx9GZiWdWiLJtPY",
    "--tab-name", "2026.06",
    "--user-entered",
    "--cells", json.dumps(cells, ensure_ascii=False)
]

import batch_write_cells
batch_write_cells.main()
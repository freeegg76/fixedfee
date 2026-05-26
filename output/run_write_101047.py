import subprocess
import sys
import json

cells = {
    "C6": "주식회사 닥터스코스메틱",
    "C7": "서울특별시 강남구 가로수길 17, 5층(신사동)",
    "C8": "608-88-00011",
    "C9": "성현철",
    "C12": "2026/06",
    "I12": "064-177713-04-036",
    "C13": "Drscosmetic-202606-Fixed-01",
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

result = subprocess.run(
    [
        sys.executable,
        r"C:\Dev\Fixed Fee\.claude\skills\sheets-writer\scripts\batch_write_cells.py",
        "--spreadsheet-id", "1iCqO5DZYUjhX0Wjc-Fn8miB_He5HIW9lT93fgK7Bj5U",
        "--tab-name", "2026.06",
        "--user-entered",
        "--cells", json.dumps(cells, ensure_ascii=False)
    ],
    capture_output=True,
    text=True,
    encoding="utf-8"
)
print(result.stdout)
if result.stderr:
    print(result.stderr, file=sys.stderr)
sys.exit(result.returncode)

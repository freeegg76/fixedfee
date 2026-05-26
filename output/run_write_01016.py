import subprocess, sys, json, os

cells = {
    "C6": "주식회사 뉴트리원",
    "C7": "서울특별시 송파구 올림픽로35다 길 42. 21,22,23층",
    "C8": "220-88-43130",
    "C9": "권진혁",
    "C12": "2026/06",
    "I12": "064-177713-04-036",
    "C13": "Nutrione-202606-Fixed-01",
    "C14": "2026/06/01",
    "C15": "2026/06/15",
    "B20": "2026/06-Service Fee",
    "D20": "2026/06/01 ~ 2026/06/30",
    "G20": 10000000,
    "E22": "KRW",
    "H23": 1000000,
    "H25": 11000000,
    "I14": ""
}

cells_json = json.dumps(cells, ensure_ascii=False)

env = os.environ.copy()
env["PYTHONUTF8"] = "1"
env["GOOGLE_SERVICE_ACCOUNT_KEY"] = "c:/Dev/Fixed Fee/credentials.json"

result = subprocess.run(
    [
        sys.executable,
        r"c:\Dev\Fixed Fee\.claude\skills\sheets-writer\scripts\batch_write_cells.py",
        "--spreadsheet-id", "17Dex0T8kshkIOWvzVNS_7pXNfO3AaBRMpq12pVAdv8g",
        "--tab-name", "2026.06",
        "--user-entered",
        "--cells", cells_json
    ],
    capture_output=True,
    text=True,
    encoding="utf-8",
    env=env,
    cwd=r"c:\Dev\Fixed Fee"
)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr, file=sys.stderr)
sys.exit(result.returncode)

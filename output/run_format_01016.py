import subprocess, sys, json, os

env = os.environ.copy()
env["PYTHONUTF8"] = "1"
env["GOOGLE_SERVICE_ACCOUNT_KEY"] = "c:/Dev/Fixed Fee/credentials.json"

result = subprocess.run(
    [
        sys.executable,
        r"c:\Dev\Fixed Fee\.claude\skills\sheets-writer\scripts\batch_write_cells.py",
        "--spreadsheet-id", "17Dex0T8kshkIOWvzVNS_7pXNfO3AaBRMpq12pVAdv8g",
        "--tab-name", "2026.06",
        "--sheet-id", "1771518132",
        "--cells", "{}",
        "--format-cells", "G20,H23,H25,H22,C16",
        "--currency", "KRW"
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

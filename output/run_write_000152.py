import subprocess, sys, json, os

cells = json.load(open("output/cells_write_000152.json", encoding="utf-8"))
cells_json = json.dumps(cells, ensure_ascii=False)

env = os.environ.copy()
env["PYTHONUTF8"] = "1"
env["GOOGLE_SERVICE_ACCOUNT_KEY"] = "c:/Dev/Fixed Fee/credentials.json"

result = subprocess.run(
    [
        sys.executable,
        ".claude/skills/sheets-writer/scripts/batch_write_cells.py",
        "--spreadsheet-id", "1obrOFgHmuI9BnCXPdYbWV9xP2tDItcxzxOrwr24Fd4g",
        "--tab-name", "2026.06",
        "--user-entered",
        "--cells", cells_json,
    ],
    env=env,
    capture_output=True,
    text=True,
    encoding="utf-8",
)
print(result.stdout)
if result.stderr:
    print(result.stderr, file=sys.stderr)
sys.exit(result.returncode)

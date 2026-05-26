import subprocess, sys, json, os

cells_path = "C:/Dev/Fixed Fee/output/cells_write_00970.json"
with open(cells_path, encoding="utf-8") as f:
    cells_data = f.read().strip()

env = os.environ.copy()
env["PYTHONUTF8"] = "1"
env["GOOGLE_SERVICE_ACCOUNT_KEY"] = "c:/Dev/Fixed Fee/credentials.json"

result = subprocess.run(
    [sys.executable,
     "C:/Dev/Fixed Fee/.claude/skills/sheets-writer/scripts/batch_write_cells.py",
     "--spreadsheet-id", "1gzHpPOb4Ms2KM9G_Zu1Ivg5MM3DMF65TqAJEUFvJ5NU",
     "--tab-name", "2026.06",
     "--user-entered",
     "--cells", cells_data],
    capture_output=True, text=True, env=env
)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr, file=sys.stderr)
sys.exit(result.returncode)

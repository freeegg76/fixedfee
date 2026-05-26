import json, sys
with open(r'C:\Dev\Fixed Fee\output\cells_write_000287.json', encoding='utf-8') as f:
    data = json.load(f)
print(json.dumps(data, ensure_ascii=False))
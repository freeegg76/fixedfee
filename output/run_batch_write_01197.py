import subprocess, sys, json

cells = {"C6":"주식회사 남유에프엔씨","C7":"서울 서초구 주흥길 20 (반포동)","C8":"303-81-79405","C9":"남유숙","C12":"2026/05","I12":"249-910029-39804","C13":"Namyu-202605-Fixed-01","C14":"2026/05/01","C15":"2026/05/15","B20":"2026/05-Service Fee","D20":"2026/05/01 ~ 2026/05/31","G20":3500000,"E22":"KRW","H23":350000,"H25":3850000,"I14":""}

import os, sys
sys.path.insert(0, r"C:\Dev\Fixed Fee\.claude\skills\sheets-writer\scripts")

os.environ["GOOGLE_SERVICE_ACCOUNT_KEY"] = "c:/Dev/Fixed Fee/credentials.json"
os.environ["PYTHONUTF8"] = "1"

from batch_write_cells import get_service, batch_write

service = get_service()
updated = batch_write(service, "1veuaVY23TPRMxsYsIAnVM-6eFffmMAXvR5P1wtxr7R4", "2026.05", cells, user_entered=True)
print(json.dumps({"updated_cells": updated}))

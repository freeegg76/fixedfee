import json, sys, os

with open(r'C:\Dev\Fixed Fee\output\cells_write_000287.json', encoding='utf-8') as f:
    cells = json.load(f)

from google.oauth2 import service_account
from googleapiclient.discovery import build

key_path = os.environ.get('GOOGLE_SERVICE_ACCOUNT_KEY')
creds = service_account.Credentials.from_service_account_file(key_path, scopes=['https://www.googleapis.com/auth/spreadsheets'])
service = build('sheets', 'v4', credentials=creds)

tab_name = '2026.06'
spreadsheet_id = '19QreH2ko4-MJxSAIlfDWQb0D7CY_vZPOjosjKVSnWXA'

data = [{'range': f"'{tab_name}'!{addr}", 'values': [[value]]} for addr, value in cells.items()]
result = service.spreadsheets().values().batchUpdate(
    spreadsheetId=spreadsheet_id,
    body={'valueInputOption': 'USER_ENTERED', 'data': data}
).execute()
print(json.dumps({'updated_cells': result.get('totalUpdatedCells', len(cells))}))
@echo off
cd /d "c:\Dev\Fixed Fee"

:: 현재 월을 YYYY/MM 형식으로 계산
for /f "tokens=*" %%i in ('powershell -command "Get-Date -Format 'yyyy/MM'"') do set RUN_MONTH=%%i

:: 환경변수 설정
set PYTHONUTF8=1
set GOOGLE_SERVICE_ACCOUNT_KEY=c:/Dev/Fixed Fee/credentials.json
set MASTER_SHEET_ID=1EVyVqFvntsWBYbeEO6Uxv2X6JbDBxP-er97WFd0U5SM
set MAX_RETRY=1

echo 고정비 인보이스 자동화 시작: %RUN_MONTH%

:: Claude Code 실행 (-p: 프롬프트 직접 전달, 비대화형 모드)
claude -p "%RUN_MONTH%" --output-format text >> "output\schedule_%RUN_MONTH:/=%.log" 2>&1

echo 완료

# 고정비 인보이스 자동화 - 월별 실행 스크립트
# 매월 25일 작업 스케줄러에 의해 자동 실행됨

Set-Location "c:\Dev\Fixed Fee"

$month    = Get-Date -Format "yyyy/MM"
$monthKey = Get-Date -Format "yyyyMM"
$logFile  = "output\scheduler_$monthKey.log"

"[$( Get-Date -Format 'yyyy-MM-dd HH:mm:ss' )] 자동 실행 시작 - 귀속월: $month" | Out-File -FilePath $logFile -Encoding utf8

claude --dangerously-skip-permissions -p "귀속월 $month 로 고정비 인보이스 자동화를 실행하라" 2>&1 | Tee-Object -FilePath $logFile -Append

"[$( Get-Date -Format 'yyyy-MM-dd HH:mm:ss' )] 자동 실행 종료" | Out-File -FilePath $logFile -Encoding utf8 -Append

@echo off
rem Resume the ladder phase-1 checks (after the 11-21 stop, and for the steps added since, e.g. known2).
rem Updates the code in C:\claude\ladder to the latest claude/ladder, then runs the checks' own launcher.
rem Every step resumes: the finished baseline is not played again. Double-click it; don't run it while a run is going.
cd /d C:\claude\ladder
if not exist C:\claude\ladder-runs\p1 mkdir C:\claude\ladder-runs\p1
rem Refuse to start while another phase-1 run is going (two at once would double the processes and share files).
powershell -NoProfile -Command "if (Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -match 'phase1_checks' }) { exit 3 } else { exit 0 }"
set CHECK=%errorlevel%
if not "%CHECK%"=="0" (
  echo not started %date% %time%: running-check returned %CHECK%, 3 means a phase-1 run is still going >> C:\claude\ladder-runs\p1\status.txt
  echo Not started: a phase-1 run is still going, or the check could not run - code %CHECK%.
  pause
  exit /b 1
)
echo pull %date% %time% >> C:\claude\ladder-runs\p1\status.txt
git pull --ff-only origin claude/ladder >> C:\claude\ladder-runs\p1\status.txt 2>&1
if errorlevel 1 (
  echo git pull failed, nothing started >> C:\claude\ladder-runs\p1\status.txt
  exit /b 1
)
git log -1 --format=commit=%%H >> C:\claude\ladder-runs\p1\status.txt
call analysis\ladder\tools\pc\phase1-checks.cmd

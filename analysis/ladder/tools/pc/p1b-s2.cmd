@echo off
rem Ladder phase-1 checks, run again under Salem's ruling S2 (11-22: never matched past 200). Double-click it once.
rem Updates the code in C:\claude\ladder to the latest claude/ladder, then runs the checks' own launcher, which writes
rem to C:\claude\ladder-runs\p1b (the 11-21 results in ...\p1 are kept). Every step resumes after a stop: double-click
rem again. Don't run it while a run is going (it checks, and refuses).
cd /d C:\claude\ladder
set RUNS=C:\claude\ladder-runs\p1b
if not exist %RUNS% mkdir %RUNS%
powershell -NoProfile -Command "if (Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -match 'phase1_checks' }) { exit 3 } else { exit 0 }"
set CHECK=%errorlevel%
if not "%CHECK%"=="0" (
  echo not started %date% %time%: running-check returned %CHECK%, 3 means a phase-1 run is still going >> %RUNS%\status.txt
  echo Not started: a phase-1 run is still going, or the check could not run - code %CHECK%.
  pause
  exit /b 1
)
echo pull %date% %time% >> %RUNS%\status.txt
git pull --ff-only origin claude/ladder >> %RUNS%\status.txt 2>&1
if errorlevel 1 (
  echo git pull failed, nothing started >> %RUNS%\status.txt
  echo git pull failed, nothing started. See %RUNS%\status.txt
  pause
  exit /b 1
)
call analysis\ladder\tools\pc\phase1-checks.cmd

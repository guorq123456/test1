@echo off
rem base-2 before phase 1's lock (RUNBOOK, first time, steps 2-3; PHASE1-REPORT section 1). Double-click once, after Salem has
rem accepted phase 1. It updates C:\claude\ladder to the latest claude/ladder, makes the host's deal key if there is
rem none (C:\claude\ladder-host\ladder.key; made once, never copied into the repository or the project folder), then
rem runs tools\base2_checks.py: keyed games and their replay, list order, p1b's logs replayed with this code, the base's
rem checks, the interface's 40 games, and a speed run on all cores. About 15 minutes. Results in
rem C:\claude\ladder-runs\base2 (summary.json); the key itself is never printed, only its id.
rem Limits: 23 worker processes + this one, no mask, below-normal priority (set by the runner).
cd /d C:\claude\ladder
set PYTHONHASHSEED=0
set PYTHONUTF8=1
set RUNS=C:\claude\ladder-runs\base2
if not exist %RUNS% mkdir %RUNS%
powershell -NoProfile -Command "if (Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -match 'phase1_checks|base2_checks|ladder\.pool|ladder\.arena' }) { exit 3 } else { exit 0 }"
set CHECK=%errorlevel%
if not "%CHECK%"=="0" (
  echo not started %date% %time%: running-check returned %CHECK%, 3 means a ladder run is still going >> %RUNS%\status.txt
  echo Not started: a ladder run is still going, or the check could not run - code %CHECK%.
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
set PYBASE=
for /f "usebackq delims=" %%p in (`.venv\Scripts\python.exe -c "import sys; print(sys._base_executable)"`) do set PYBASE=%%p
set __PYVENV_LAUNCHER__=%CD%\.venv\Scripts\python.exe
"%PYBASE%" -c "import sys, numpy; assert sys.prefix != sys.base_prefix" >nul 2>&1
if errorlevel 1 (
  set PYBASE=%CD%\.venv\Scripts\python.exe
  set __PYVENV_LAUNCHER__=
  echo real interpreter does not see the venv, using the venv launcher >> %RUNS%\status.txt
)
echo started base-2 checks %date% %time% with %PYBASE% >> %RUNS%\status.txt
git log -1 --format=commit=%%H >> %RUNS%\status.txt
"%PYBASE%" analysis\ladder\tools\base2_checks.py --runs %RUNS% --p1b C:\claude\ladder-runs\p1b --make-key --workers 23 >> %RUNS%\log.txt 2>&1
echo finished %date% %time% exit %errorlevel% >> %RUNS%\status.txt
echo Done. Results: %RUNS%\summary.json
pause

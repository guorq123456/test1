@echo off
rem Dry run of one player period before the players come in (tools/arena_dry.py; PLAN 8a/8b, A50, A52-A55). Double-click
rem once. It updates C:\claude\ladder to the latest claude/ladder, then plays a throwaway deck period under
rem C:\claude\ladder-runs\arena-dry\<commit>: a small pool of the seven baseline lists, the arena opened for 8 minutes,
rem the collection loop taking four submissions of two made-up players (one refused, one late) while one of them
rem practises, 150 pool games, the replay audit, the formal games handed to each one's folder, the compute
rem ratio's own noise on the E-cores (1200 games, 1200 replays), the players' commands on a cp1252 console,
rem the compute check on the pool's own games. About 35 minutes. Results in C:\claude\ladder-runs\arena-dry\summary.json.
rem The real pool, ledger, arena and player folders are not touched. The host's key is used, never printed.
rem Limits: 23 worker processes + this one (15 on the E-cores where compute is compared), below-normal priority.
cd /d C:\claude\ladder
set PYTHONHASHSEED=0
set PYTHONUTF8=1
set RUNS=C:\claude\ladder-runs\arena-dry
if not exist %RUNS% mkdir %RUNS%
powershell -NoProfile -Command "if (Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -match 'phase1_checks|base2_checks|arena_dry|ladder\.pool|ladder\.arena|ladder\.collect|ladder\.submit' }) { exit 3 } else { exit 0 }"
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
echo started arena dry run %date% %time% with %PYBASE% >> %RUNS%\status.txt
git log -1 --format=commit=%%H >> %RUNS%\status.txt
"%PYBASE%" analysis\ladder\tools\arena_dry.py --runs %RUNS% --workers 23 >> %RUNS%\log.txt 2>&1
echo finished %date% %time% exit %errorlevel% >> %RUNS%\status.txt
echo Done. Results: %RUNS%\summary.json
pause

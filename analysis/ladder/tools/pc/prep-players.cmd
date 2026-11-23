@echo off
rem Before the players come in (RUNBOOK first time 4-5; PLAN 8, items 2.2 and 2.5). Double-click once. It updates
rem C:\claude\ladder to the latest claude/ladder, then:
rem 1. tools\first_setup.py: the official pool (the p1b baseline pool copied whole to C:\claude\ladder-host\pool, the
rem    original untouched, then advanced into period 1), the host's folders, the players' folders
rem    C:\claude\ladder-players\<pinyin>\submit and receipts, and C:\claude\ladder-players\public (the repo's public\).
rem    Run again, it changes nothing that is already right.
rem 2. tools\pilot_conditions.py (2.5): the five trained pilots in the ladder's condition (default guess) and their own
rem    (known lists), 50 games against each of the bot's 12 other lists, each game also played by the default bot
rem    on the pilot's list; E-cores only (it compares per-step compute), 15 workers. About an hour.
rem 3. tools\lethal_bank.py (2.2): the lethal puzzle bank, 300 games of the default against itself on the public lists,
rem    every turn start searched in full, every lethal played out by the default behind the base; all cores. About 20
rem    minutes. Then Salem's own lethal puzzle (tests\puzzles).
rem Results under C:\claude\ladder-runs\prep\<commit>\ (setup\summary.json, pilots\result.json, lethal\*-summary.json).
rem The host's key is used (only its id is written). Limits: below-normal priority; 23 worker processes at most.
cd /d C:\claude\ladder
set PYTHONHASHSEED=0
set PYTHONUTF8=1
set RUNS=C:\claude\ladder-runs\prep
if not exist %RUNS% mkdir %RUNS%
powershell -NoProfile -Command "if (Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -match 'phase1_checks|base2_checks|arena_dry|first_setup|pilot_conditions|lethal_bank|ladder\.pool|ladder\.arena|ladder\.collect|ladder\.submit' }) { exit 3 } else { exit 0 }"
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
for /f "usebackq delims=" %%c in (`git rev-parse --short HEAD`) do set C=%%c
set OUT=%RUNS%\%C%
if not exist %OUT% mkdir %OUT%
echo started %date% %time% commit %C% with %PYBASE% >> %RUNS%\status.txt
"%PYBASE%" analysis\ladder\tools\first_setup.py --out %OUT%\setup >> %OUT%\log.txt 2>&1
set E1=%errorlevel%
echo setup exit %E1% %date% %time% >> %RUNS%\status.txt
if not "%E1%"=="0" (
  echo The setup did not pass: see %OUT%\setup\summary.json. Nothing else started.
  pause
  exit /b 1
)
"%PYBASE%" analysis\ladder\tools\pilot_conditions.py --seeds 93170000 93176000 --games-per-opponent 50 --workers 15 --mask 0x3FC3FC --out %OUT%\pilots >> %OUT%\log.txt 2>&1
echo pilots exit %errorlevel% %date% %time% >> %RUNS%\status.txt
"%PYBASE%" analysis\ladder\tools\lethal_bank.py --source ladder --seeds 93162000 93162300 --games 300 --workers 23 --out %OUT%\lethal >> %OUT%\log.txt 2>&1
echo lethal ladder exit %errorlevel% %date% %time% >> %RUNS%\status.txt
"%PYBASE%" analysis\ladder\tools\lethal_bank.py --source bank --workers 3 --out %OUT%\lethal >> %OUT%\log.txt 2>&1
echo lethal bank exit %errorlevel% %date% %time% >> %RUNS%\status.txt
echo finished %date% %time% >> %RUNS%\status.txt
echo Done. Results: %OUT%
pause

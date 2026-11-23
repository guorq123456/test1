@echo off
rem Opening a period (RUNBOOK every period 1 and 3): tools\open_period.py. It checks the locked files and the key,
rem freezes the pool, writes the anchor table, snapshots the arena and opens its window (4 hours, 20000 games),
rem writes the period's report into C:\claude\ladder-players\public\reports, then runs the collection loop until
rem the deadline and after it until the period is collected ("zhe yi qi shou wan"). Keep this window open till then.
rem Started again while the window is open, it never opens a second window: it goes straight to the loop.
rem A strategy period's gate margin is kept in C:\claude\ladder-host\gates\delta-P<period>.json (RUNBOOK 1.3).
rem With "dry" as the first argument: a dry run under C:\claude\ladder-runs\open-dry\ on a copy of the pool,
rem a 3-minute window, no game played, no seed used; the real pool, arena and player folders are not touched.
rem This file does not pull: the wrapper in C:\claude\ladder-runs pulls only when no window is open (players'
rem runs import the code; RUNBOOK: no pull while running).
rem The running-check looks only for the host's own processes: players' practice (ladder.arena, precheck) is fine.
cd /d C:\claude\ladder
set PYTHONHASHSEED=0
set PYTHONUTF8=1
set DRY=
if /i "%~1"=="dry" set DRY=--dry
if defined DRY (set RUNS=C:\claude\ladder-runs\open-dry) else (set RUNS=C:\claude\ladder-runs\open)
if not exist %RUNS% mkdir %RUNS%
powershell -NoProfile -Command "if (Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -match 'phase1_checks|base2_checks|arena_dry|first_setup|open_period|pilot_conditions|lethal_bank|ladder\.pool|ladder\.collect|ladder\.submit (receive|gate|admit|deliver)|ladder\.(anchors|puzzles|audit|compute_audit|outside)' }) { exit 3 } else { exit 0 }"
set CHECK=%errorlevel%
if not "%CHECK%"=="0" goto busy
if defined DRY goto go
echo This opens the period NOW: the 4-hour window starts and the players can begin.
echo If the window is already open, it only restarts the collection loop.
set OK=
set /p OK=Type OPEN and press Enter to go on: 
if not "%OK%"=="OPEN" goto nothing
powershell -NoProfile -Command "if (Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -match 'phase1_checks|base2_checks|arena_dry|first_setup|open_period|pilot_conditions|lethal_bank|ladder\.pool|ladder\.collect|ladder\.submit (receive|gate|admit|deliver)|ladder\.(anchors|puzzles|audit|compute_audit|outside)' }) { exit 3 } else { exit 0 }"
set CHECK=%errorlevel%
if not "%CHECK%"=="0" goto busy
:go
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
for /f "usebackq delims=" %%t in (`powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"`) do set T=%%t
set OUT=%RUNS%\%T%-%C%
if not exist %OUT% mkdir %OUT%
echo started %date% %time% commit %C% %DRY% with %PYBASE% out %OUT% >> %RUNS%\status.txt
"%PYBASE%" analysis\ladder\tools\open_period.py --out %OUT% %DRY%
set E1=%errorlevel%
echo open_period exit %E1% %date% %time% >> %RUNS%\status.txt
if not "%E1%"=="0" goto failed
echo Done. Results: %OUT%\summary.json
pause
exit /b 0
:failed
echo Did not finish cleanly: see %OUT%\summary.json and %OUT%\commands.log.
pause
exit /b 1
:busy
echo not started %date% %time%: running-check returned %CHECK%, 3 means a host run is still going >> %RUNS%\status.txt
echo Not started: a host run is still going, or the check could not run - code %CHECK%.
pause
exit /b 1
:nothing
echo Nothing done.
pause
exit /b 1

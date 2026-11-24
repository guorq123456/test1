@echo off
rem Closing a period (RUNBOOK every period 4-6): tools\close_period.py. After the deadline, once the collection loop
rem has said the period is collected and stopped: the ladder until the period is done, the hall of fame, the anchor
rem games, the puzzles due (START after period 1), the replay audit, the compute spot check, the players' formal
rem games, the leaderboards, and the advance to the next period if nothing held it. Every step can be run again: a
rem second double-click goes on from where the first stopped. Keep this window open until it says Done.
rem This file does not pull: the wrapper in C:\claude\ladder-runs pulls only after the deadline, with no host run going.
cd /d C:\claude\ladder
set PYTHONHASHSEED=0
set PYTHONUTF8=1
set RUNS=C:\claude\ladder-runs\close
if not exist %RUNS% mkdir %RUNS%
powershell -NoProfile -Command "if (Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -match 'phase1_checks|base2_checks|arena_dry|first_setup|open_period|close_period|pilot_conditions|lethal_bank|ladder\.pool|ladder\.collect|ladder\.submit (receive|gate|admit|deliver)|ladder\.(anchors|puzzles|audit|compute_audit|outside|leaderboard)|ladder\.arena formal' }) { exit 3 } else { exit 0 }"
set CHECK=%errorlevel%
if not "%CHECK%"=="0" goto busy
echo This closes the period: the ladder, the anchors, the audits, and then the pool goes to the next period.
set OK=
set /p OK=Type CLOSE and press Enter to go on:
if not "%OK%"=="CLOSE" goto nothing
powershell -NoProfile -Command "if (Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -match 'phase1_checks|base2_checks|arena_dry|first_setup|open_period|close_period|pilot_conditions|lethal_bank|ladder\.pool|ladder\.collect|ladder\.submit (receive|gate|admit|deliver)|ladder\.(anchors|puzzles|audit|compute_audit|outside|leaderboard)|ladder\.arena formal' }) { exit 3 } else { exit 0 }"
set CHECK=%errorlevel%
if not "%CHECK%"=="0" goto busy
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
echo started %date% %time% commit %C% with %PYBASE% out %OUT% >> %RUNS%\status.txt
"%PYBASE%" analysis\ladder\tools\close_period.py --out %OUT%
set E1=%errorlevel%
echo close_period exit %E1% %date% %time% >> %RUNS%\status.txt
if "%E1%"=="0" goto done
if "%E1%"=="2" goto held
echo Did not finish cleanly: see %OUT%\summary.json and %OUT%\commands.log.
pause
exit /b 1
:done
echo Done. Results: %OUT%\summary.json
pause
exit /b 0
:held
echo Held before the advance, for the host to look at: see "held" in %OUT%\summary.json.
pause
exit /b 2
:busy
echo not started %date% %time%: running-check returned %CHECK%, 3 means a host run is still going >> %RUNS%\status.txt
echo Not started: a host run is still going (the collection loop?), or the check could not run - code %CHECK%.
pause
exit /b 1
:nothing
echo Nothing done.
pause
exit /b 1

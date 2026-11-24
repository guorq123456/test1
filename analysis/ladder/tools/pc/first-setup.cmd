@echo off
rem The setup again, alone (RUNBOOK first time 4-6): tools\first_setup.py checks the locked files and the key, finds
rem the official pool already in period 1 (never copied over), refreshes C:\claude\ladder-players\public from the
rem repo's public\, and adds the starting puzzle START (2.6, Salem S19: Haven, bot/T1-HAVEN-1) if it is not there yet. Plays no game,
rem uses no seed, takes a few seconds. Results under C:\claude\ladder-runs\setup\<commit>\summary.json.
cd /d C:\claude\ladder
set PYTHONHASHSEED=0
set PYTHONUTF8=1
set RUNS=C:\claude\ladder-runs\setup
if not exist %RUNS% mkdir %RUNS%
powershell -NoProfile -Command "if (Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -match 'phase1_checks|base2_checks|arena_dry|first_setup|open_period|close_period|pilot_conditions|lethal_bank|ladder\.pool|ladder\.arena|ladder\.collect|ladder\.submit' }) { exit 3 } else { exit 0 }"
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
rem compiled copies made before the 11-23 docstring changes still hold the old text (players read this folder)
if exist analysis\ladder\ladder\__pycache__ rd /s /q analysis\ladder\ladder\__pycache__
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
"%PYBASE%" analysis\ladder\tools\first_setup.py --out %OUT% >> %OUT%\log.txt 2>&1
set E1=%errorlevel%
echo setup exit %E1% %date% %time% >> %RUNS%\status.txt
if not "%E1%"=="0" (
  echo The setup did not pass: see %OUT%\summary.json.
  pause
  exit /b 1
)
echo finished %date% %time% >> %RUNS%\status.txt
echo Done. Results: %OUT%\summary.json
pause

@echo off
rem Ladder phase-1 checks on Salem's computer (host tooling, analysis/ladder/tools/phase1_checks.py). Every step resumes.
rem 11-22: run again under Salem's ruling S2 (never matched past 200) into C:\claude\ladder-runs\p1b. The 11-21 run in
rem C:\claude\ladder-runs\p1 (old matching) stays as it is; its baseline seeds are excluded from the new baseline.
rem Start it by double-clicking or with explorer.exe, outside the Claude app, so closing the app doesn't stop it.
rem Limits: 11 worker processes + this one = 12, E-cores only (mask 0x3FC3FC), below-normal priority (set by the runner).
rem The venv's python.exe is only a launcher that starts the real interpreter as a second process, so it would make 13.
rem Start the real interpreter directly, telling it which venv it belongs to the way multiprocessing does for its
rem workers (__PYVENV_LAUNCHER__, bpo-35797); check it really sees the venv, else fall back to the launcher and say so.
rem PYTHONUTF8=1: logs and files in UTF-8 (Windows' default cp1252 can't write Chinese; the 11-21 run stopped on that).
cd /d C:\claude\ladder
set PYTHONHASHSEED=0
set PYTHONUTF8=1
set RUNS=C:\claude\ladder-runs\p1b
if not exist %RUNS% mkdir %RUNS%
rem Refuse to start while another phase-1 run is going (two at once would double the processes and share files).
powershell -NoProfile -Command "if (Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -match 'phase1_checks' }) { exit 3 } else { exit 0 }"
set CHECK=%errorlevel%
if not "%CHECK%"=="0" (
  echo not started %date% %time%: running-check returned %CHECK%, 3 means a phase-1 run is still going >> %RUNS%\status.txt
  echo Not started: a phase-1 run is still going, or the check could not run - code %CHECK%.
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
  echo real interpreter does not see the venv, using the venv launcher: 13 processes >> %RUNS%\status.txt
)
echo started %date% %time% with %PYBASE% >> %RUNS%\status.txt
git log -1 --format=commit=%%H >> %RUNS%\status.txt
"%PYBASE%" -c "import sys; print('prefix', sys.prefix, 'executable', sys.executable)" >> %RUNS%\status.txt 2>&1
"%PYBASE%" analysis\ladder\tools\phase1_checks.py all --runs %RUNS% --exclude-pool C:\claude\ladder-runs\p1\baseline\pool --workers 11 --mask 0x3FC3FC >> %RUNS%\log.txt 2>&1
echo finished %date% %time% exit %errorlevel% >> %RUNS%\status.txt

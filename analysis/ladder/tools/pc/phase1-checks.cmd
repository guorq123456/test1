@echo off
rem Ladder phase-1 checks on Salem's computer (host tooling, analysis/ladder/tools/phase1_checks.py).
rem Start it by double-clicking or with explorer.exe, outside the Claude app, so closing the app doesn't stop it.
rem Limits: 11 worker processes + this one = 12, E-cores only (mask 0x3FC3FC), below-normal priority (set by the runner).
rem The venv's python.exe is only a launcher that starts the real interpreter as a second process, so it would make 13.
rem Start the real interpreter directly, telling it which venv it belongs to the way multiprocessing does for its
rem workers (__PYVENV_LAUNCHER__, bpo-35797). If that can't be found, fall back to the venv launcher and say so.
cd /d C:\claude\ladder
set PYTHONHASHSEED=0
if not exist C:\claude\ladder-runs\p1 mkdir C:\claude\ladder-runs\p1
set PYBASE=
for /f "usebackq delims=" %%p in (`.venv\Scripts\python.exe -c "import sys; print(sys._base_executable)"`) do set PYBASE=%%p
set __PYVENV_LAUNCHER__=%CD%\.venv\Scripts\python.exe
if not exist "%PYBASE%" (
  set PYBASE=%CD%\.venv\Scripts\python.exe
  set __PYVENV_LAUNCHER__=
  echo real interpreter not found, using the venv launcher: 13 processes >> C:\claude\ladder-runs\p1\status.txt
)
echo started %date% %time% with %PYBASE% >> C:\claude\ladder-runs\p1\status.txt
"%PYBASE%" -c "import sys; print('prefix', sys.prefix, 'executable', sys.executable)" >> C:\claude\ladder-runs\p1\status.txt 2>&1
"%PYBASE%" analysis\ladder\tools\phase1_checks.py all --runs C:\claude\ladder-runs\p1 --workers 11 --mask 0x3FC3FC >> C:\claude\ladder-runs\p1\log.txt 2>&1
echo finished %date% %time% exit %errorlevel% >> C:\claude\ladder-runs\p1\status.txt

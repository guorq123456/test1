@echo off
rem 11-24, S31: period 2's three updates whose gate stopped with an error (S-0046, S-0054, S-0061) recorded as not
rem passed, without new games (Salem's decision card, 20:48Z). Needs the code from after period 2's close: run
rem C:\claude\ladder-runs\before-P3.cmd first (it pulls). No pull here, no game, no seed.
rem 1. a dry run: reads the ledgers, checks every receipt (the error, the attempt's games, the version it was against),
rem    writes nothing: C:\claude\ladder-runs\settle-P2\dry\summary.json;
rem 2. if it found no problem: type WRITE to write (gate ledger, submissions ledger, the players' receipts):
rem    C:\claude\ladder-runs\settle-P2\write\summary.json. A receipt written once is refused the second time.
cd /d C:\claude\ladder
if not exist analysis\ladder\tools\gate_settle.py goto nocode
set PYTHONHASHSEED=0
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set PYBASE=
for /f "usebackq delims=" %%p in (`.venv\Scripts\python.exe -c "import sys; print(sys._base_executable)"`) do set PYBASE=%%p
set __PYVENV_LAUNCHER__=%CD%\.venv\Scripts\python.exe
"%PYBASE%" -c "import sys, numpy; assert sys.prefix != sys.base_prefix" >nul 2>&1
if errorlevel 1 (
  set PYBASE=%CD%\.venv\Scripts\python.exe
  set __PYVENV_LAUNCHER__=
)
set OUT=C:\claude\ladder-runs\settle-P2
if not exist %OUT% mkdir %OUT%
"%PYBASE%" analysis\ladder\tools\gate_settle.py S-0046 S-0054 S-0061 --out %OUT%\dry
set E1=%errorlevel%
echo dry exit %E1% %date% %time% >> %OUT%\status.txt
if not "%E1%"=="0" goto problems
set /p W=Type WRITE (capitals) to write it, anything else to stop: 
if not "%W%"=="WRITE" goto stopped
"%PYBASE%" analysis\ladder\tools\gate_settle.py S-0046 S-0054 S-0061 --out %OUT%\write --write
set E2=%errorlevel%
echo write exit %E2% %date% %time% >> %OUT%\status.txt
if not "%E2%"=="0" goto problems
echo Done: %OUT%\write\summary.json
pause
exit /b
:problems
echo Problems found, nothing written: see the lines above and %OUT%\dry\summary.json (or write\).
pause
exit /b 1
:stopped
echo Stopped, nothing written.
pause
exit /b 1
:nocode
echo tools\gate_settle.py is not here yet: run C:\claude\ladder-runs\before-P3.cmd first (it pulls).
pause
exit /b 1

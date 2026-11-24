@echo off
rem Salem's lab (ladder.lab, S30; guide: C:\claude\ladder\analysis\ladder\LAB.md): his own practice interface, apart
rem from the players' arena: all cores (23 workers), no game cap, no window, everything visible. From a terminal:
rem   C:\claude\ladder-lab\lab.cmd field
rem   C:\claude\ladder-lab\lab.cmd decks --find RUNE
rem   C:\claude\ladder-lab\lab.cmd vs --deck bot/T3-RUNE-1 --strategy bot:mcts:400+plan --class dragon --games 400
rem   C:\claude\ladder-lab\lab.cmd vs --version D:\my\v1 --vs-deck ps11b/RUNE-CR-x --games 1000
rem   C:\claude\ladder-lab\lab.cmd vs --version D:\my\v2 --same-as L0002
rem   C:\claude\ladder-lab\lab.cmd ladder --version D:\my\v2
rem   C:\claude\ladder-lab\lab.cmd replay --run L0002 --game L0002-00003 --seat 0
rem Results in C:\claude\ladder-lab\runs\. It runs on the code in C:\claude\ladder as it is (no pull), and queues
rem with the players for the machine: one run at a time (the host's own work first).
setlocal
set PYTHONHASHSEED=0
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set PYTHONPATH=C:\claude\ladder;C:\claude\ladder\analysis\ladder
set VPY=C:\claude\ladder\.venv\Scripts\python.exe
set PYBASE=
for /f "usebackq delims=" %%p in (`%VPY% -c "import sys; print(sys._base_executable)"`) do set PYBASE=%%p
set __PYVENV_LAUNCHER__=%VPY%
"%PYBASE%" -c "import sys, numpy; assert sys.prefix != sys.base_prefix" >nul 2>&1
if errorlevel 1 (
  set PYBASE=%VPY%
  set __PYVENV_LAUNCHER__=
)
"%PYBASE%" -m ladder.lab %*
exit /b %errorlevel%

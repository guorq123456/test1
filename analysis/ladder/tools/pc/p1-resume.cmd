@echo off
rem Resume the ladder phase-1 checks after the 11-21 stop (encoding error after the baseline step).
rem Updates the code in C:\claude\ladder to the latest claude/ladder, then runs the checks' own launcher.
rem Every step resumes: the finished baseline is not played again. Double-click it; don't run it while a run is going.
cd /d C:\claude\ladder
if not exist C:\claude\ladder-runs\p1 mkdir C:\claude\ladder-runs\p1
echo pull %date% %time% >> C:\claude\ladder-runs\p1\status.txt
git pull --ff-only origin claude/ladder >> C:\claude\ladder-runs\p1\status.txt 2>&1
if errorlevel 1 (
  echo git pull failed, nothing started >> C:\claude\ladder-runs\p1\status.txt
  exit /b 1
)
git log -1 --format=commit=%%H >> C:\claude\ladder-runs\p1\status.txt
call analysis\ladder\tools\pc\phase1-checks.cmd

@echo off
rem Ladder phase-1 checks on Salem's computer (host tooling, analysis/ladder/tools/phase1_checks.py).
rem Start it by double-clicking or with explorer.exe, outside the Claude app, so closing the app doesn't stop it.
rem Limits: 11 worker processes + this one, E-cores only (mask 0x3FC3FC), below-normal priority (set by the runner).
cd /d C:\claude\ladder
set PYTHONHASHSEED=0
if not exist C:\claude\ladder-runs\p1 mkdir C:\claude\ladder-runs\p1
echo started %date% %time% >> C:\claude\ladder-runs\p1\status.txt
.venv\Scripts\python.exe analysis\ladder\tools\phase1_checks.py all --runs C:\claude\ladder-runs\p1 --workers 11 --mask 0x3FC3FC >> C:\claude\ladder-runs\p1\log.txt 2>&1
echo finished %date% %time% exit %errorlevel% >> C:\claude\ladder-runs\p1\status.txt

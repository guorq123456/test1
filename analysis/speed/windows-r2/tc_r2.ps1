[Console]::OutputEncoding = [Text.Encoding]::UTF8
$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
$env:PYTHONPATH = '.;analysis\speed;analysis\turn-level;analysis\card-value'; $env:PYTHONIOENCODING = 'utf-8'; $env:PYTHONUTF8 = '1'
Set-Location C:\claude\test1-speed-r2
$R = 'C:\claude\svsim-data\speed-out-r2'
$out = & 'C:\claude\test1\.venv\Scripts\python.exe' -m svsim.tools.host turn_cost C:/claude/test1/analysis/turn-level/step1 --n 60 --a level-max --b level-strong --out "$R\speed_cost_rerun.jsonl" 2>&1 | ForEach-Object { "$_" }
$rc = $LASTEXITCODE
$out | Set-Content -Encoding utf8 "$R\turn_cost_new_rerun.txt"
$out
if (-not ($out -match 'host: priority below normal, mask 0xffffe, 19 CPUs')) { "HOST LINE MISSING"; exit 1 }
exit $rc

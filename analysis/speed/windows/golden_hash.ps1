[Console]::OutputEncoding = [Text.Encoding]::UTF8
$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
$env:PYTHONPATH = '.;C:\claude\svsim-data\speed-probe'; $env:PYTHONIOENCODING = 'utf-8'; $env:PYTHONUTF8 = '1'
$py = 'C:\claude\test1\.venv\Scripts\python.exe'
foreach ($p in @(@('old','C:\claude\test1-speed-old'), @('new','C:\claude\test1-speed-new'))) {
  Set-Location $p[1]
  $out = & $py -m svsim.tools.host golden_hash 2>&1 | ForEach-Object { "$_" }
  if (-not ($out -match 'host: priority below normal, mask 0xffffe, 19 CPUs')) { "HOST LINE MISSING"; exit 1 }
  if ($LASTEXITCODE -ne 0) { $out; exit 1 }
  $out | Where-Object { $_ -notmatch '^host:' } | Set-Content -Encoding utf8 "C:\claude\svsim-data\speed-out\golden_hash_$($p[0]).txt"
  "== $($p[0])"; $out | Where-Object { $_ -notmatch '^host:' }
}

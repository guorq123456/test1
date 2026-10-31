$pidFile = 'C:\claude\svwb-tracker\archiver.pid'
if (-not (Test-Path $pidFile)) { 'no pid file'; return }
$p = Get-Process -Id ([int](Get-Content $pidFile)) -ErrorAction SilentlyContinue
if ($p -and $p.Name -eq 'powershell') { Stop-Process -Id $p.Id; "stopped pid=$($p.Id)" } else { 'not running' }
Remove-Item $pidFile

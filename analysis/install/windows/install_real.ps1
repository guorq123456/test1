# Real install, checklist section 7, in the arena checkout C:\claude\test1 (merge 7f2c751, code = 3ba425e).
Set-Location C:\claude\test1
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$PSDefaultParameterValues['Add-Content:Encoding'] = 'utf8'
$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
$env:PYTHONPATH = '.;analysis\speed;C:\claude\test1-install\analysis\turn-level;C:\claude\test1-install\analysis\card-value;C:\claude\svsim-data\speed-probe'; $env:PYTHONIOENCODING = 'utf-8'; $env:PYTHONUTF8 = '1'
$me = Get-Process -Id $PID; $me.ProcessorAffinity = [IntPtr]0xFFFFE; $me.PriorityClass = 'BelowNormal'
$py = 'C:\claude\test1\.venv\Scripts\python.exe'
$log = 'C:\claude\svsim-data\log-install-real.txt'
$S = 'C:/claude/test1/analysis/turn-level/step1'
$R = 'C:\claude\svsim-data\install-real'; New-Item -ItemType Directory -Force $R | Out-Null
function Run([string]$tag, [string[]]$argv, [switch]$Host_) {
  $t0 = Get-Date
  $out = & $py @argv 2>&1 | ForEach-Object { "$_" }
  $rc = $LASTEXITCODE
  "=== $tag ===" | Add-Content $log; $out | Add-Content $log
  "$tag done in $([math]::Round(((Get-Date)-$t0).TotalMinutes,1)) min; exit $rc" | Add-Content $log
  $out | Set-Content -Encoding utf8 "$R\$tag.txt"
  if ($Host_ -and -not ($out -match 'host: priority below normal, mask 0xffffe, 19 CPUs')) { "HOST LINE MISSING - stop" | Add-Content $log; exit 1 }
  if ($rc -ne 0) { "$tag FAILED (exit $rc) - stop" | Add-Content $log; exit 1 }
  return $out
}
"install start $(Get-Date -Format s) on $(git log -1 --format=%h)" | Add-Content $log
Run 'cmp_roots_before' @('-m','svsim.tools.host','cmp_roots',$S) -Host_ | Out-Null
Run 'golden_hash' @('-m','svsim.tools.host','golden_hash') -Host_ | Out-Null
Run 'max_smoke' @('-m','svsim.tools.host','svsim.tools.gate','--a','level-max','--b','level-strong','--deck','ramp','--opponent','ramp','--fixed','--max','2','--seed','69900010','--workers','2','--out',"$R\max_smoke.jsonl") -Host_ | Out-Null
Run 'apply' @('analysis\install\strong_kc_xprune.py','apply') | Out-Null
Run 'smoke' @('-m','svsim.tools.host','analysis.install.strong_kc_xprune_smoke','--workers','3') -Host_ | Out-Null
Run 'pytest_pkg' @('-m','pytest','-q','-p','no:cacheprovider','tests\test_web.py','tests\test_learn.py','tests\test_xprune.py','tests\test_install_packages.py') | Out-Null
"INSTALLED" | Add-Content $log
Run 'check_after' @('analysis\install\strong_kc_xprune.py','check') | Out-Null
Run 'cmp_roots_after' @('-m','svsim.tools.host','cmp_roots',$S) -Host_ | Out-Null
"install end $(Get-Date -Format s)" | Add-Content $log

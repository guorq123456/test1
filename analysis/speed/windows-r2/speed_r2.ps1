# Speed round 2 check on Windows: old c5413b3 (test1-speed-new) vs new b215e3d (test1-speed-r2), analysis 552156e. One process at a time.
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$PSDefaultParameterValues['Add-Content:Encoding'] = 'utf8'
$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
$env:PYTHONPATH = '.;analysis\speed;analysis\turn-level;analysis\card-value;C:\claude\svsim-data\speed-probe'; $env:PYTHONIOENCODING = 'utf-8'; $env:PYTHONUTF8 = '1'
$py = 'C:\claude\test1\.venv\Scripts\python.exe'
$log = 'C:\claude\svsim-data\log-speed-r2.txt'
$S = 'C:/claude/test1/analysis/turn-level/step1'
$OLD = 'C:\claude\test1-speed-new'; $NEW = 'C:\claude\test1-speed-r2'
$R = 'C:\claude\svsim-data\speed-out-r2'; New-Item -ItemType Directory -Force $R | Out-Null
function RunHost([string]$wt, [string]$tag, [string[]]$argv, [switch]$MayFail) {
  Set-Location $wt
  $t0 = Get-Date
  $out = & $py -m svsim.tools.host @argv 2>&1 | ForEach-Object { "$_" }
  $rc = $LASTEXITCODE
  "=== $tag ($wt) ===" | Add-Content $log; $out | Add-Content $log
  "$tag done in $([math]::Round(((Get-Date)-$t0).TotalMinutes,1)) min; exit $rc" | Add-Content $log
  if (-not ($out -match 'host: priority below normal, mask 0xffffe, 19 CPUs')) { "HOST LINE MISSING - stop" | Add-Content $log; exit 1 }
  $out | Where-Object { $_ -notmatch '^host:' } | Set-Content -Encoding utf8 "$R\$tag.txt"
  if ($rc -ne 0) { if ($MayFail) { "$tag exit $rc (recorded, continuing)" | Add-Content $log } else { "$tag FAILED (exit $rc) - stop" | Add-Content $log; exit 1 } }
  return $out
}

$inl = & $py -c "import sys; sys.path.insert(0, r'$NEW'); import svsim.core.view as v; print(sys.version.split()[0], v._INLINE)"
"python / _INLINE (new): $inl" | Add-Content $log; "python / _INLINE (new): $inl" | Set-Content -Encoding utf8 "$R\env.txt"
"r2 check start $(Get-Date -Format s); old $OLD (c5413b3), new $NEW (b215e3d)" | Add-Content $log
# 1. Behaviour
RunHost $OLD 'cmp_roots_old' @('cmp_roots', $S) | Out-Null
RunHost $NEW 'cmp_roots_new' @('cmp_roots', $S) | Out-Null
RunHost $OLD 'golden_hash_old' @('golden_hash') | Out-Null
RunHost $NEW 'golden_hash_new' @('golden_hash') | Out-Null
$env:SVSIM_COW_CHECK = '1'
RunHost $NEW 'cmp_roots_new_cow' @('cmp_roots', $S) | Out-Null
RunHost $NEW 'golden_hash_new_cow' @('golden_hash') | Out-Null
Remove-Item Env:SVSIM_COW_CHECK
$env:SVSIM_STEP1_DIR = $S
RunHost $NEW 'tests_lethal_enums_cow' @('pytest', 'tests/test_lethal_same.py', 'tests/test_enums.py', 'tests/test_cow.py', '-q', '-p', 'no:cacheprovider', '-rs') -MayFail | Out-Null
RunHost $NEW 'tests_full' @('pytest', 'tests', '-q', '-p', 'no:cacheprovider', '-rs') -MayFail | Out-Null
Remove-Item Env:SVSIM_STEP1_DIR
# 2. Speed
foreach ($k in 1..3) {
  RunHost $OLD "bench_old_$k" @('bench', $S, '30', '3') | Out-Null
  RunHost $NEW "bench_new_$k" @('bench', $S, '30', '3') | Out-Null
}
RunHost $NEW 'turn_cost_new' @('turn_cost', $S, '--n', '60', '--a', 'level-max', '--b', 'level-strong', '--out', "$R\speed_cost.jsonl") | Out-Null
"r2 check end $(Get-Date -Format s)" | Add-Content $log

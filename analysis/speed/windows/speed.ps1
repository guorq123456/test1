# Speed check on Windows: old cefd7c1 vs new c5413b3 (worktrees test1-speed-old / test1-speed-new), analysis 552156e. One process at a time.
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$PSDefaultParameterValues['Add-Content:Encoding'] = 'utf8'
$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
$env:PYTHONPATH = '.;analysis\speed;analysis\turn-level;analysis\card-value'; $env:PYTHONIOENCODING = 'utf-8'; $env:PYTHONUTF8 = '1'
$py = 'C:\claude\test1\.venv\Scripts\python.exe'
$log = 'C:\claude\svsim-data\log-speed.txt'
$S = 'C:/claude/test1/analysis/turn-level/step1'
$OLD = 'C:\claude\test1-speed-old'; $NEW = 'C:\claude\test1-speed-new'
$R = 'C:\claude\svsim-data\speed-out'; New-Item -ItemType Directory -Force $R | Out-Null
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
"speed check start $(Get-Date -Format s)" | Add-Content $log
# 1b. Golden tests on new and old (frozen on Linux; reference only)
RunHost $NEW 'tests_new' @('pytest', 'tests/test_enums.py', 'tests/test_golden_search.py', '-q', '-p', 'no:cacheprovider') -MayFail | Out-Null
RunHost $OLD 'tests_old' @('pytest', 'tests/test_golden_search.py', '-q', '-p', 'no:cacheprovider') -MayFail | Out-Null
# 2. Speed: alternate old/new, three times each (each bench.py = warm-up + 3 rounds of 30 starts)
foreach ($k in 1..3) {
  RunHost $OLD "bench_old_$k" @('bench', $S, '30', '3') | Out-Null
  RunHost $NEW "bench_new_$k" @('bench', $S, '30', '3') | Out-Null
}
# 3. Per-turn cost on new code, same 60 starts as split_cost
Set-Location $NEW
RunHost $NEW 'turn_cost_new' @('turn_cost', $S, '--n', '60', '--a', 'mcts:200+plan+learned+phased+pickd8i200m0z1kstr', '--b', 'level-strong', 'mcts:1043+plan+learned+phased', '--out', "$R\speed_cost.jsonl") | Out-Null
"speed check end $(Get-Date -Format s)" | Add-Content $log

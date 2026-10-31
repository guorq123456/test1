# Archives Shadowverse WB crash-reporter breadcrumbs (rolling buffer) into raw\breadcrumbs-YYYY-MM-DD.jsonl.
# Read-only on the game files (opened with FileShare.ReadWrite). Never exits on errors.
$ErrorActionPreference = 'Continue'
$root = 'C:\claude\svwb-tracker'
$bt = 'C:\Program Files\Epic Games\ShadowverseWorldsBeyONv4y\ShadowverseWB_Data\Persistent\bt'
$files = @("$bt\bt-breadcrumbs-0", "$bt\bt-breadcrumbs-1")
$logFile = "$root\logs\archiver.log"
$utf8 = New-Object System.Text.UTF8Encoding($false)
$maxKeys = 5000
$seen = New-Object 'System.Collections.Generic.HashSet[string]'
$order = New-Object 'System.Collections.Generic.Queue[string]'
$stamp = @{}

function Log($msg) {
  try { [IO.File]::AppendAllText($logFile, (Get-Date).ToString('yyyy-MM-dd HH:mm:ss') + " $msg`r`n", $utf8) } catch {}
}
function Remember($key) {
  if (-not $seen.Add($key)) { return $false }
  $order.Enqueue($key)
  while ($order.Count -gt $maxKeys) { [void]$seen.Remove($order.Dequeue()) }
  return $true
}
function ReadShared($path) {
  $fs = [IO.File]::Open($path, 'Open', 'Read', 'ReadWrite,Delete')
  try { $sr = New-Object IO.StreamReader($fs, $utf8); return $sr.ReadToEnd() } finally { $fs.Dispose() }
}
# Each entry is one JSON object; the game writes one per line. Returns compact entry strings, or $null if the file is unusable this round.
function Entries($text) {
  $out = New-Object System.Collections.Generic.List[string]
  $lines = $text -split "`r?`n"
  if ($lines.Count -ge 3) {
    foreach ($l in $lines) {
      $t = $l.Trim()
      if (-not $t.StartsWith('{')) { continue }
      $t = $t.TrimEnd(',')
      if ($seen.Contains($t)) { continue }
      try { $o = $t | ConvertFrom-Json; if ($null -ne $o.timestamp) { $out.Add($t) } } catch {}  # partial line: pick it up next round
    }
  } else {
    try { $arr = $text | ConvertFrom-Json } catch { return $null }
    foreach ($o in $arr) { $out.Add(($o | ConvertTo-Json -Compress -Depth 10)) }
  }
  return ,$out
}

# Seed keys from today's archive so a restart does not duplicate entries.
$today = "$root\raw\breadcrumbs-" + (Get-Date).ToString('yyyy-MM-dd') + '.jsonl'
if (Test-Path $today) { try { Get-Content $today -Encoding UTF8 -Tail $maxKeys | % { [void](Remember $_) } } catch {} }
Log "start pid=$PID seeded=$($seen.Count)"

while ($true) {
  foreach ($f in $files) {
    try {
      $fi = New-Object IO.FileInfo($f)
      if (-not $fi.Exists) { continue }
      $sig = "$($fi.Length)|$($fi.LastWriteTimeUtc.Ticks)"
      if ($stamp[$f] -eq $sig) { continue }
      $entries = Entries (ReadShared $f)
      if ($null -eq $entries) { continue }  # unparsable now; retry next round
      $new = New-Object System.Text.StringBuilder
      $n = 0
      foreach ($e in $entries) { if (Remember $e) { [void]$new.Append($e).Append("`n"); $n++ } }
      if ($n -gt 0) {
        $out = "$root\raw\breadcrumbs-" + (Get-Date).ToString('yyyy-MM-dd') + '.jsonl'
        [IO.File]::AppendAllText($out, $new.ToString(), $utf8)
        Log "$([IO.Path]::GetFileName($f)): +$n"
      }
      $stamp[$f] = $sig
    } catch { Log "error $([IO.Path]::GetFileName($f)): $($_.Exception.Message)" }
  }
  Start-Sleep -Seconds 5
}

# Archives Shadowverse WB crash-reporter breadcrumbs (rolling buffer) into raw\breadcrumbs-YYYY-MM-DD.jsonl.
# Read-only on the game files (opened with FileShare.ReadWrite). Never exits on errors.
# When a battle result appears it screenshots the result screen (rank gauge) into shots\, only while shots\ENABLED exists.
param([string]$TestShot)  # -TestShot <path>: take one screenshot with the same code and exit
$ErrorActionPreference = 'Continue'
$root = 'C:\claude\svwb-tracker'
$shots = "$root\shots"
Add-Type -AssemblyName System.Drawing, System.Windows.Forms
Add-Type -Namespace Win32 -Name Dpi -MemberDefinition '[DllImport("user32.dll")] public static extern bool SetProcessDPIAware();'
[void][Win32.Dpi]::SetProcessDPIAware()  # physical pixels (1920x1200), not the 125% scaled size
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

# Passive full-screen capture of the primary screen (GDI copy; nothing is sent to the game).
function Capture($path) {
  $b = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
  $bmp = New-Object System.Drawing.Bitmap($b.Width, $b.Height)
  try {
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    try { $g.CopyFromScreen($b.Location, [System.Drawing.Point]::Empty, $b.Size) } finally { $g.Dispose() }
    $bmp.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
  } finally { $bmp.Dispose() }
}
if ($TestShot) { Capture $TestShot; return }
$pending = New-Object System.Collections.Generic.List[object]  # @{due=epoch ms; path=...}
function NowMs { [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds() }
# A result line was just archived: shoot at +3 s and +4 s (rank gauge page) and +8 s (last page) after the line's own timestamp.
function ScheduleShots($entry) {
  if (-not (Test-Path "$shots\ENABLED")) { return }
  if ($entry -notmatch '"timestamp":\s*(\d+)') { return }
  $ts = [int64]$Matches[1]
  $age = (NowMs) - $ts
  if ($age -gt 30000) { return }  # old line found after a restart, not a live result
  $name = "$shots\result-" + [DateTimeOffset]::FromUnixTimeMilliseconds($ts).LocalDateTime.ToString('yyyyMMdd-HHmmss')
  if ($age -gt 4000) { $pending.Add(@{ due = 0; path = "$name-late.png" }) }
  else { $pending.Add(@{ due = $ts + 3000; path = "$name-a.png" }); $pending.Add(@{ due = $ts + 4000; path = "$name-b.png" }) }
  $pending.Add(@{ due = $ts + 8000; path = "$name-c.png" })
  $script:lastResult = NowMs
  Log "result seen (age $age ms), shots scheduled"
}
function RunDueShots {
  $now = NowMs
  foreach ($p in @($pending | ? { $_.due -le $now })) {
    try { Capture $p.path; Log "shot $([IO.Path]::GetFileName($p.path))" } catch { Log "shot failed: $($_.Exception.Message)" }
    [void]$pending.Remove($p)
  }
}
function PruneShots {
  try { Get-ChildItem $shots -Filter *.png | ? { $_.LastWriteTime -lt (Get-Date).AddDays(-14) } | Remove-Item -ErrorAction SilentlyContinue } catch {}
}
$lastResult = 0
$lastPrune = [datetime]::MinValue
$lastProcCheck = [datetime]::MinValue
$gameRunning = $false

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
      foreach ($e in $entries) {
        if (Remember $e) {
          [void]$new.Append($e).Append("`n"); $n++
          if ($e.Contains('PlayTimeline, name=BattleResult')) { ScheduleShots $e }
        }
      }
      if ($n -gt 0) {
        $out = "$root\raw\breadcrumbs-" + (Get-Date).ToString('yyyy-MM-dd') + '.jsonl'
        [IO.File]::AppendAllText($out, $new.ToString(), $utf8)
        Log "$([IO.Path]::GetFileName($f)): +$n"
      }
      $stamp[$f] = $sig
    } catch { Log "error $([IO.Path]::GetFileName($f)): $($_.Exception.Message)" }
  }
  RunDueShots
  if (((Get-Date) - $lastPrune).TotalHours -ge 1) { PruneShots; $lastPrune = Get-Date }
  if (((Get-Date) - $lastProcCheck).TotalSeconds -ge 30) {
    $gameRunning = [bool](Get-Process -Name ShadowverseWB -ErrorAction SilentlyContinue); $lastProcCheck = Get-Date
  }
  # Poll every 1 s while the game runs (so the +3 s shot is not missed), 250 ms while shots are due, else 5 s.
  if ($pending.Count -gt 0) { Start-Sleep -Milliseconds 250 }
  elseif ($gameRunning -or ((NowMs) - $lastResult) -lt 10000) { Start-Sleep -Seconds 1 }
  else { Start-Sleep -Seconds 5 }
}

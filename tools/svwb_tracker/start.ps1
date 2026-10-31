# Starts archiver.ps1 hidden, lowest priority, E-cores only (affinity 0xFC3C). Does nothing if already running.
$root = 'C:\claude\svwb-tracker'
$pidFile = "$root\archiver.pid"
if (Test-Path $pidFile) {
  $old = Get-Process -Id ([int](Get-Content $pidFile)) -ErrorAction SilentlyContinue
  if ($old -and $old.Name -eq 'powershell') { "already running pid=$($old.Id)"; return }
}
$p = Start-Process powershell -WindowStyle Hidden -PassThru -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File',"$root\archiver.ps1"
$p.PriorityClass = 'Idle'
$p.ProcessorAffinity = [IntPtr]0xFC3C
$p.Id | Set-Content $pidFile
"started pid=$($p.Id)"

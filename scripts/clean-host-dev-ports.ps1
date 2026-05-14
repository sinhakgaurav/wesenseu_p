<#
.SYNOPSIS
  Stop host processes listening on common *app* dev ports (Python/Node only).
  Does not stop Docker or database containers (Postgres/Redis keep running).
#>
$ErrorActionPreference = "SilentlyContinue"
$ports = @(8000, 8001, 8002, 3000, 3001, 3002, 5173, 8080)
$allowNames = @("python", "python3", "pythonw", "node")

foreach ($port in $ports) {
  $conns = @(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
  foreach ($c in $conns) {
    $id = $c.OwningProcess
    $p = Get-Process -Id $id -ErrorAction SilentlyContinue
    if (-not $p) { continue }
    $name = $p.ProcessName
    if ($allowNames -contains $name) {
      Write-Host "Stopping $name (PID $id) on port $port"
      Stop-Process -Id $id -Force -ErrorAction SilentlyContinue
    } else {
      Write-Host "Skipping port $port PID $id ($name) — not python/node (leave Docker/system alone)"
    }
  }
}
Write-Host "Done."

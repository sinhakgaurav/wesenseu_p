<#
.SYNOPSIS
  Stop Monitour/WesenseU *application* containers only; leave Postgres + Redis running.
  Use when you want Docker DB/cache but local uvicorn/vite on 8000/8001/3000.
#>
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root
docker compose stop backend frontend celery_worker wesenseu wesenseu_worker
Write-Host "App containers stopped. Databases still running: db, redis, wesenseu_db, wesenseu_redis"

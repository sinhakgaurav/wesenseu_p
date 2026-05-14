<#
.SYNOPSIS
  Bring databases up if needed, then start all app containers (full Docker stack).
#>
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root
docker compose up -d db redis wesenseu_db wesenseu_redis
docker compose up -d wesenseu wesenseu_worker backend celery_worker frontend
Write-Host "Full stack starting. Use: docker compose ps"

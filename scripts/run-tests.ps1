# Run Monitour backend integration + frontend unit/e2e tests.
# Prerequisite: docker compose up (backend :8000, frontend :3000)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root

Write-Host "=== Backend integration tests ===" -ForegroundColor Cyan
docker compose exec -T backend pip install -q -r requirements-dev.txt 2>$null
docker compose exec -T -e MONITOUR_API_URL=http://localhost:8000 backend pytest tests/ -v --tb=short
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`n=== Frontend unit tests (vitest) ===" -ForegroundColor Cyan
Set-Location "$root/frontend"
if (-not (Test-Path node_modules)) { npm install }
npm run test
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`n=== Frontend E2E (Playwright) ===" -ForegroundColor Cyan
npx playwright install chromium 2>$null
$env:PLAYWRIGHT_BASE_URL = "http://localhost:3000"
npm run test:e2e
exit $LASTEXITCODE

# PowerShell dev helper — run from project root: .\scripts\dev.ps1

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null
Set-Location (Split-Path $PSScriptRoot -Parent)

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example"
}

$python = if (Test-Path ".\.venv\Scripts\python.exe") { ".\.venv\Scripts\python.exe" } else { "python" }

Write-Host "Running pytest..."
& $python -m pytest backend/tests -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Smoke test (start backend separately if needed)..."
Write-Host "Backend: http://127.0.0.1:8000  (if port blocked, use 8010)"
Write-Host ""
Write-Host "  Optional reset: .\scripts\reset_dev_db.ps1"
Write-Host "  Terminal 1: $python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"
Write-Host "  Terminal 2: $python scripts/smoke_mvp.py"
Write-Host "  Godot: open client/ and press F5"

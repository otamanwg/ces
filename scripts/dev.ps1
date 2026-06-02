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

Write-Host "Starting backend if needed..."
& ".\scripts\start_backend.ps1"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Running HTTP MVP smoke..."
& $python scripts/smoke_mvp.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "Dev backend is ready at http://127.0.0.1:8000"
Write-Host "Optional reset: .\scripts\reset_dev_db.ps1"
Write-Host "Godot: open client/ and press F5"

# One-click dev launch for City Economic Simulator
# Usage: .\scripts\play.ps1

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

$env:PATH = "C:\tools\dotnet;C:\tools\MinGit\cmd;" + $env:PATH

$python = if (Test-Path ".\.venv\Scripts\python.exe") { ".\.venv\Scripts\python.exe" } else { "python" }
$godot = "C:\tools\Godot\Godot_v4.2.2-stable_mono_win64\Godot_v4.2.2-stable_mono_win64.exe"

if (-not (Test-Path $godot)) {
    Write-Host "Godot not found at $godot"
    exit 1
}

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
}

Write-Host "Building Godot C# project..."
Push-Location client
dotnet build city_economic_simulator.csproj -c Debug -v q
Pop-Location

$backendUp = $false
try {
    $r = Invoke-WebRequest -Uri "http://127.0.0.1:8000/" -TimeoutSec 2
    if ($r.StatusCode -eq 200) { $backendUp = $true }
} catch {}

if (-not $backendUp) {
    Write-Host "Starting backend in new window..."
    Start-Process powershell -ArgumentList @(
        "-NoExit", "-Command",
        "cd '$Root'; & '$python' -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"
    )
    Start-Sleep -Seconds 3
}

Write-Host "Opening Godot project..."
Write-Host "Press F5 in Godot to play."
Start-Process $godot -ArgumentList @("--path", "$Root\client")

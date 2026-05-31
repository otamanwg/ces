param(
    [switch]$Foreground
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\godot_mcp_bridge.py"
$LogDir = Join-Path $Root ".tools\logs"
$OutLog = Join-Path $LogDir "godot-mcp-bridge.out.log"
$ErrLog = Join-Path $LogDir "godot-mcp-bridge.err.log"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

if (-not (Test-Path $Python)) {
    throw "Python venv not found at $Python"
}

if ($Foreground) {
    & $Python $Script
    exit $LASTEXITCODE
}

$existing = Get-NetTCPConnection -LocalPort 6505 -State Listen -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Godot MCP bridge already listening on 6505."
    exit 0
}

Start-Process -FilePath $Python `
    -ArgumentList @($Script) `
    -WorkingDirectory $Root `
    -WindowStyle Hidden `
    -RedirectStandardOutput $OutLog `
    -RedirectStandardError $ErrLog

Start-Sleep -Seconds 1
Write-Host "Godot MCP bridge started."
Write-Host "HTTP control: http://127.0.0.1:6507/status"
Write-Host "Logs: $OutLog"

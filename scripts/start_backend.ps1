param(
    [int]$Port = 8000,
    [int]$TimeoutSeconds = 30,
    [switch]$Foreground
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null

$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example"
}

$python = if (Test-Path ".\.venv\Scripts\python.exe") { ".\.venv\Scripts\python.exe" } else { "python" }
$baseUrl = "http://127.0.0.1:$Port"

function Test-BackendReady {
    try {
        $response = Invoke-WebRequest -Uri "$baseUrl/" -TimeoutSec 2
        return $response.StatusCode -eq 200
    } catch {
        return $false
    }
}

if (Test-BackendReady) {
    Write-Host "Backend already running at $baseUrl"
    exit 0
}

$argsList = @(
    "-m", "uvicorn", "backend.main:app",
    "--host", "127.0.0.1",
    "--port", "$Port",
    "--reload"
)

if ($Foreground) {
    & $python @argsList
    exit $LASTEXITCODE
}

$logDir = Join-Path $Root ".tools\logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$outLog = Join-Path $logDir "backend.out.log"
$errLog = Join-Path $logDir "backend.err.log"

Write-Host "Starting backend at $baseUrl ..."
Start-Process -FilePath $python `
    -ArgumentList $argsList `
    -WorkingDirectory $Root `
    -WindowStyle Hidden `
    -RedirectStandardOutput $outLog `
    -RedirectStandardError $errLog

$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
while ((Get-Date) -lt $deadline) {
    if (Test-BackendReady) {
        Write-Host "Backend ready at $baseUrl"
        Write-Host "Logs: $outLog"
        exit 0
    }
    Start-Sleep -Seconds 1
}

Write-Host "Backend did not become ready within $TimeoutSeconds seconds."
Write-Host "stdout: $outLog"
Write-Host "stderr: $errLog"
exit 1

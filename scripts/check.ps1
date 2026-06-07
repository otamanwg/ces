param(
    [switch]$SkipClient
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$env:CITY_DATABASE_URL = if ($env:CITY_DATABASE_URL) {
    $env:CITY_DATABASE_URL
} else {
    "postgresql+psycopg2://city:city_dev_password@127.0.0.1:5432/city_game"
}

$env:CITY_TEST_DATABASE_URL = if ($env:CITY_TEST_DATABASE_URL) {
    $env:CITY_TEST_DATABASE_URL
} else {
    "postgresql+psycopg2://city:city_dev_password@127.0.0.1:5432/city_game_test"
}

$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "Python venv not found at $python. Run backend setup first."
}

Write-Host "== Alembic upgrade =="
& $python -m alembic upgrade head
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "== Backend tests =="
& $python -m pytest backend\tests -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if (-not $SkipClient) {
    $dotnet = "C:\tools\dotnet-sdk\dotnet.exe"
    if (-not (Test-Path $dotnet)) {
        $dotnet = "dotnet"
    }

    Write-Host "== Client logic tests =="
    & $dotnet run --project client_tests\ClientLogicTests.csproj -c Debug
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    Write-Host "== Client build =="
    & $dotnet build client\city_economic_simulator.csproj -c Debug -v minimal
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Write-Host "All checks passed."

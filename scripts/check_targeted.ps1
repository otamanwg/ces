param(
    [ValidateSet(
        "list",
        "backend-fast",
        "auth",
        "economy",
        "buildings",
        "scheduler",
        "observability",
        "districts",
        "npcs",
        "prod-fast",
        "prod-smoke",
        "client",
        "client-smoke",
        "full"
    )]
    [string]$Profile = "list"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

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

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "Python venv not found at $Python. Run backend setup first."
}

$Dotnet = "C:\tools\dotnet-sdk\dotnet.exe"
if (-not (Test-Path $Dotnet)) {
    $Dotnet = "dotnet"
}

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,

        [Parameter(Mandatory = $true)]
        [scriptblock]$Command
    )

    Write-Host "== $Name =="
    & $Command
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

function Invoke-Alembic {
    Invoke-Step "Alembic upgrade" { & $Python -m alembic upgrade head }
}

function Invoke-PythonStatic {
    Invoke-Step "Python lint" { & $Python -m ruff check backend\app backend\main.py }
    Invoke-Step "Python format check" { & $Python -m ruff format --check backend\app backend\main.py }
    Invoke-Step "Python typecheck" { & $Python -m pyright backend\app backend\main.py }
}

function Invoke-SecretScan {
    Invoke-Step "Secret scan" { & $Python scripts\check_secrets.py }
}

function Invoke-Pytest {
    param([string[]]$Paths)
    Invoke-Step "Backend targeted tests" { & $Python -m pytest @Paths -q }
}

function Invoke-ClientLogic {
    Invoke-Step "Client logic tests" { & $Dotnet run --project client_tests\ClientLogicTests.csproj -c Debug }
}

function Invoke-ClientBuild {
    Invoke-Step "Client build" { & $Dotnet build client\city_economic_simulator.csproj -c Debug -v minimal }
}

function Show-Profiles {
    Write-Host "Available targeted profiles:"
    Write-Host "  backend-fast  Alembic + Ruff + pyright + secrets + lightweight backend tests."
    Write-Host "  auth          Auth/session/WebSocket API tests."
    Write-Host "  economy       Core loop, economy balance, 30-day gate, player progress."
    Write-Host "  buildings     Land/buildings/business/mayor policy tests."
    Write-Host "  scheduler     Scheduler leader lock and lifecycle tests."
    Write-Host "  observability Health, metrics, request id/logging tests."
    Write-Host "  districts     Phase G1+ dynamic district metrics, seasonality, radar API."
    Write-Host "  npcs          Phase G2+ NPC residents: hire, payroll, spending, API."
    Write-Host "  prod-fast     Production config/lifecycle/health tests + Compose config validation."
    Write-Host "  prod-smoke    Isolated production Compose smoke with migration, readiness, metrics, Prometheus/Grafana."
    Write-Host "  client        Client logic tests + Godot C# build."
    Write-Host "  client-smoke  Client profile + headless Godot API dispatch runtime smoke."
    Write-Host "  full          Existing scripts/check.ps1 full local gate."
}

switch ($Profile) {
    "list" {
        Show-Profiles
    }
    "backend-fast" {
        Invoke-Alembic
        Invoke-PythonStatic
        Invoke-SecretScan
        Invoke-Pytest @(
            "backend\tests\test_app_exceptions.py",
            "backend\tests\test_health.py",
            "backend\tests\test_metrics.py",
            "backend\tests\test_observability.py",
            "backend\tests\test_production_config.py",
            "backend\tests\test_city_news.py",
            "backend\tests\test_player_progress.py"
        )
    }
    "auth" {
        Invoke-Alembic
        Invoke-PythonStatic
        Invoke-Pytest @(
            "backend\tests\test_api_mvp_loop.py",
            "backend\tests\test_onboarding_api.py",
            "backend\tests\test_websocket_lifecycle.py"
        )
    }
    "economy" {
        Invoke-Alembic
        Invoke-PythonStatic
        Invoke-Pytest @(
            "backend\tests\test_mvp_loop.py",
            "backend\tests\test_economy_balance.py",
            "backend\tests\test_economy_30_day_gate.py",
            "backend\tests\test_player_progress.py"
        )
    }
    "buildings" {
        Invoke-Alembic
        Invoke-PythonStatic
        Invoke-Pytest @(
            "backend\tests\test_land_building_api.py",
            "backend\tests\test_business_management.py",
            "backend\tests\test_mayor_policy.py"
        )
    }
    "scheduler" {
        Invoke-Alembic
        Invoke-PythonStatic
        Invoke-Pytest @(
            "backend\tests\test_scheduler.py",
            "backend\tests\test_lifecycle.py"
        )
    }
    "observability" {
        Invoke-Alembic
        Invoke-PythonStatic
        Invoke-Pytest @(
            "backend\tests\test_observability.py",
            "backend\tests\test_metrics.py",
            "backend\tests\test_health.py"
        )
    }
    "districts" {
        Invoke-Alembic
        Invoke-PythonStatic
        Invoke-Pytest @(
            "backend\tests\test_district_metrics.py"
        )
    }
    "npcs" {
        Invoke-Alembic
        Invoke-PythonStatic
        Invoke-Pytest @(
            "backend\tests\test_npc_service.py",
            "backend\tests\test_district_metrics.py"
        )
    }
    "prod-fast" {
        Invoke-Alembic
        Invoke-PythonStatic
        Invoke-SecretScan
        Invoke-Pytest @(
            "backend\tests\test_production_config.py",
            "backend\tests\test_lifecycle.py",
            "backend\tests\test_health.py"
        )
        Invoke-Step "Production Compose config" {
            docker compose --env-file .env.production.example -f docker-compose.prod.yml config --quiet
        }
    }
    "prod-smoke" {
        Invoke-Step "Production smoke" {
            & "$Root\scripts\pwsh7.ps1" -NoProfile -File "$Root\scripts\smoke_production.ps1"
        }
    }
    "client" {
        Invoke-ClientLogic
        Invoke-ClientBuild
    }
    "client-smoke" {
        Invoke-ClientLogic
        Invoke-ClientBuild
        Invoke-Step "Client API dispatch runtime smoke" {
            & "$Root\scripts\pwsh7.ps1" -NoProfile -File "$Root\scripts\smoke_client_api_dispatch.ps1" -SkipBuild
        }
    }
    "full" {
        Invoke-Step "Full local gate" {
            & "$Root\scripts\pwsh7.ps1" -NoProfile -File "$Root\scripts\check.ps1"
        }
    }
}

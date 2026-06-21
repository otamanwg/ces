param(
    [string]$ProjectName = "ces-backup-restore-drill",
    [string]$BackupPath = "",
    [string]$RestoreDatabase = "city_restore_drill",
    [string]$ExpectedRowCounts = "",
    [switch]$ValidateExistingBackup,
    [switch]$KeepStack
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if ($ValidateExistingBackup -and -not $BackupPath) {
    throw "-BackupPath is required when -ValidateExistingBackup is set."
}

if (-not $BackupPath) {
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $BackupPath = Join-Path $root ".cache\backups\ces-prod-drill-$timestamp.sql"
}

$backupDirectory = Split-Path -Parent $BackupPath
if ($backupDirectory) {
    New-Item -ItemType Directory -Force -Path $backupDirectory | Out-Null
}

$secretDir = Join-Path $root ".cache\backup-restore-secrets"
New-Item -ItemType Directory -Force -Path $secretDir | Out-Null
$postgresPasswordFile = Join-Path $secretDir "postgres_password.txt"
$redisPasswordFile = Join-Path $secretDir "redis_password.txt"
$grafanaPasswordFile = Join-Path $secretDir "grafana_admin_password.txt"
$databaseUrlFile = Join-Path $secretDir "city_database_url.txt"
$redisUrlFile = Join-Path $secretDir "redis_url.txt"

$postgresPassword = "drillLocalPostgresSecret2026!"
$redisPassword = "drillLocalRedisSecret2026!"
$grafanaPassword = "drillLocalGrafanaSecret2026!"
Set-Content -NoNewline -Encoding UTF8 -Path $postgresPasswordFile -Value $postgresPassword
Set-Content -NoNewline -Encoding UTF8 -Path $redisPasswordFile -Value $redisPassword
Set-Content -NoNewline -Encoding UTF8 -Path $grafanaPasswordFile -Value $grafanaPassword
Set-Content -NoNewline -Encoding UTF8 -Path $databaseUrlFile -Value "postgresql+psycopg2://city:$postgresPassword@postgres:5432/city_game"
Set-Content -NoNewline -Encoding UTF8 -Path $redisUrlFile -Value "redis://:$redisPassword@redis:6379/0"

$env:POSTGRES_USER = "city"
$env:POSTGRES_PASSWORD_FILE = $postgresPasswordFile
$env:POSTGRES_DB = "city_game"
$env:REDIS_PASSWORD_FILE = $redisPasswordFile
$env:CITY_DATABASE_URL_FILE = $databaseUrlFile
$env:REDIS_URL_FILE = $redisUrlFile
$env:CITY_CORS_ORIGINS = "https://drill.example"
$env:CITY_RELEASE_SHA = "drill-release-sha"
$env:CITY_RELEASE_IMAGE = "ces-backend:drill"
$env:CITY_RELEASE_VERSION = "0.3.0-drill"
$env:BACKEND_PORT = "18100"
$env:PROMETHEUS_PORT = "18190"
$env:GRAFANA_PORT = "18191"
$env:GRAFANA_ADMIN_USER = "admin"
$env:GRAFANA_ADMIN_PASSWORD_FILE = $grafanaPasswordFile

$composeArgs = @(
    "--project-name", $ProjectName,
    "-f", "docker-compose.prod.yml"
)

function Invoke-Compose {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
    docker compose @composeArgs @Args
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose $($Args -join ' ') failed with exit code $LASTEXITCODE."
    }
}

function Invoke-PostgresScalar {
    param(
        [Parameter(Mandatory = $true)][string]$Database,
        [Parameter(Mandatory = $true)][string]$Sql
    )

    $result = docker compose @composeArgs exec -T postgres psql `
        -U $env:POSTGRES_USER `
        -d $Database `
        -tAc $Sql
    if ($LASTEXITCODE -ne 0) {
        throw "PostgreSQL scalar query failed: $Sql"
    }
    return $result.Trim()
}

function Get-TableCounts {
    param([Parameter(Mandatory = $true)][string]$Database)

    $tables = @(
        "alembic_version",
        "cities",
        "city_metrics",
        "city_economy_snapshots"
    )

    $counts = @{}
    foreach ($table in $tables) {
        $counts[$table] = [int](Invoke-PostgresScalar -Database $Database -Sql "SELECT COUNT(*) FROM $table;")
    }
    return $counts
}

function Convert-ExpectedRowCounts {
    param([string]$Raw)

    $counts = @{}
    if ([string]::IsNullOrWhiteSpace($Raw)) {
        return $counts
    }

    foreach ($entry in $Raw.Split(",", [System.StringSplitOptions]::RemoveEmptyEntries)) {
        $parts = $entry.Split("=", 2, [System.StringSplitOptions]::TrimEntries)
        if ($parts.Count -ne 2 -or -not $parts[0]) {
            throw "Invalid ExpectedRowCounts entry '$entry'. Use table=count pairs, for example cities=5,players=100."
        }
        $counts[$parts[0]] = [int]$parts[1]
    }
    return $counts
}

try {
    Write-Host "== Start isolated production database =="
    Invoke-Compose up -d --wait postgres

    $sourceCounts = $null

    if (-not $ValidateExistingBackup) {
        Write-Host "== Build migration image =="
        Invoke-Compose build migrate

        Write-Host "== Apply migrations =="
        Invoke-Compose run --rm migrate

        Write-Host "== Seed restore validation sentinel data =="
        $sentinelSql = @"
WITH city_row AS (
    INSERT INTO cities (
        id,
        name,
        treasury_balance,
        tax_rate_income,
        tax_rate_property,
        inflation_rate,
        game_day
    )
    VALUES (
        '00000000-0000-0000-0000-000000000101',
        'Restore Drill City',
        50000.00,
        10.00,
        2.00,
        0.00,
        2
    )
    ON CONFLICT (name) DO UPDATE SET game_day = EXCLUDED.game_day
    RETURNING id
)
INSERT INTO city_metrics (
    id,
    city_id,
    gdp_per_capita,
    unemployment_rate,
    business_density,
    startup_success_rate,
    average_business_profit,
    crime_rate,
    happiness_index,
    education_level,
    social_mobility,
    infrastructure_quality,
    traffic_index,
    environmental_score,
    inflation_rate,
    property_price_index,
    consumer_spending
)
SELECT
    '00000000-0000-0000-0000-000000000102',
    id,
    1000.00,
    10.00,
    5.00,
    60.00,
    500.00,
    5.00,
    70.00,
    60.00,
    50.00,
    70.00,
    50.00,
    75.00,
    0.00,
    100.00,
    50000.00
FROM city_row
ON CONFLICT (city_id) DO UPDATE SET consumer_spending = EXCLUDED.consumer_spending;

INSERT INTO city_economy_snapshots (
    id,
    city_id,
    game_day,
    active_money_supply,
    previous_active_money_supply,
    target_growth_rate,
    money_growth_rate,
    inflation_rate
)
VALUES (
    '00000000-0000-0000-0000-000000000103',
    '00000000-0000-0000-0000-000000000101',
    2,
    1234.56,
    NULL,
    0.0300,
    0.0000,
    0.00
)
ON CONFLICT (city_id, game_day) DO UPDATE SET active_money_supply = EXCLUDED.active_money_supply;
"@
        $sentinelSql | docker compose @composeArgs exec -T postgres psql `
            -v ON_ERROR_STOP=1 `
            -U $env:POSTGRES_USER `
            -d $env:POSTGRES_DB
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to seed restore validation sentinel data."
        }

        $sourceCounts = Get-TableCounts -Database $env:POSTGRES_DB

        Write-Host "== Create PostgreSQL dump =="
        docker compose @composeArgs exec -T postgres pg_dump `
            -U $env:POSTGRES_USER `
            -d $env:POSTGRES_DB `
            --no-owner `
            --no-privileges |
            Set-Content -Encoding UTF8 -Path $BackupPath
        if ($LASTEXITCODE -ne 0) {
            throw "pg_dump failed with exit code $LASTEXITCODE."
        }
    } else {
        Write-Host "== Validate existing backup file =="
    }

    $backupFile = Get-Item -LiteralPath $BackupPath
    if ($backupFile.Length -le 0) {
        throw "Backup file '$BackupPath' is empty."
    }

    Write-Host "== Restore dump into validation database =="
    Invoke-Compose exec -T postgres dropdb -U $env:POSTGRES_USER --if-exists $RestoreDatabase
    Invoke-Compose exec -T postgres createdb -U $env:POSTGRES_USER $RestoreDatabase
    Get-Content -Raw -LiteralPath $BackupPath |
        docker compose @composeArgs exec -T postgres psql `
            -v ON_ERROR_STOP=1 `
            -U $env:POSTGRES_USER `
            -d $RestoreDatabase
    if ($LASTEXITCODE -ne 0) {
        throw "psql restore failed with exit code $LASTEXITCODE."
    }

    Write-Host "== Validate restored schema =="
    $migrationHead = docker compose @composeArgs exec -T postgres psql `
        -U $env:POSTGRES_USER `
        -d $RestoreDatabase `
        -tAc "SELECT version_num FROM alembic_version;"
    if ($LASTEXITCODE -ne 0 -or -not $migrationHead) {
        throw "Could not read alembic_version from restored database."
    }

    $snapshotTable = docker compose @composeArgs exec -T postgres psql `
        -U $env:POSTGRES_USER `
        -d $RestoreDatabase `
        -tAc "SELECT to_regclass('public.city_economy_snapshots');"
    if ($LASTEXITCODE -ne 0 -or ($snapshotTable.Trim() -ne "city_economy_snapshots")) {
        throw "Restored database is missing city_economy_snapshots."
    }

    Write-Host "== Validate restored row counts =="
    $restoredCounts = Get-TableCounts -Database $RestoreDatabase
    if ($sourceCounts -ne $null) {
        foreach ($table in $sourceCounts.Keys) {
            if ($sourceCounts[$table] -ne $restoredCounts[$table]) {
                throw "Restored row count mismatch for '$table': source=$($sourceCounts[$table]) restored=$($restoredCounts[$table])."
            }
        }
    }

    $expectedCounts = Convert-ExpectedRowCounts $ExpectedRowCounts
    foreach ($table in $expectedCounts.Keys) {
        if (-not $restoredCounts.ContainsKey($table)) {
            throw "Expected row count table '$table' is not tracked by this drill."
        }
        if ($restoredCounts[$table] -ne $expectedCounts[$table]) {
            throw "Restored row count mismatch for '$table': expected=$($expectedCounts[$table]) restored=$($restoredCounts[$table])."
        }
    }

    if (-not $ValidateExistingBackup) {
        $sentinelMoneySupply = Invoke-PostgresScalar `
            -Database $RestoreDatabase `
            -Sql "SELECT active_money_supply::text FROM city_economy_snapshots WHERE id = '00000000-0000-0000-0000-000000000103';"
        if ($sentinelMoneySupply -ne "1234.56") {
            throw "Restored sentinel economy snapshot mismatch: active_money_supply=$sentinelMoneySupply."
        }
    }

    Write-Host "Backup restore drill passed."
    Write-Host "Backup: $BackupPath"
    Write-Host "Restored migration head: $($migrationHead.Trim())"
    foreach ($table in ($restoredCounts.Keys | Sort-Object)) {
        Write-Host "Restored rows ${table}: $($restoredCounts[$table])"
    }
}
finally {
    if (-not $KeepStack) {
        Write-Host "== Remove backup restore drill stack =="
        docker compose @composeArgs down --volumes --remove-orphans
    }
}

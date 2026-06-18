param(
    [string]$EnvFile = ".env.production",
    [string]$ProjectName = "ces-prod-rollout-preflight",
    [switch]$SkipBackupDrill,
    [switch]$SkipSmoke,
    [switch]$AllowExampleEnv
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

function Read-DotEnv {
    param([Parameter(Mandatory = $true)][string]$Path)

    $values = @{}
    foreach ($line in Get-Content -LiteralPath $Path) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith("#")) {
            continue
        }

        $separator = $trimmed.IndexOf("=")
        if ($separator -le 0) {
            continue
        }

        $key = $trimmed.Substring(0, $separator).Trim()
        $value = $trimmed.Substring($separator + 1).Trim().Trim('"').Trim("'")
        $values[$key] = $value
    }

    return $values
}

function Assert-EnvValue {
    param(
        [Parameter(Mandatory = $true)][hashtable]$Values,
        [Parameter(Mandatory = $true)][string]$Name
    )

    if (-not $Values.ContainsKey($Name) -or [string]::IsNullOrWhiteSpace($Values[$Name])) {
        throw "$Name is required in $EnvFile."
    }
}

function Assert-StrongSecret {
    param(
        [Parameter(Mandatory = $true)][hashtable]$Values,
        [Parameter(Mandatory = $true)][string]$Name
    )

    $value = ""
    $fileName = "${Name}_FILE"
    if ($Values.ContainsKey($fileName) -and -not [string]::IsNullOrWhiteSpace($Values[$fileName])) {
        $secretPath = Resolve-SecretPath $Values[$fileName]
        if (-not (Test-Path -LiteralPath $secretPath)) {
            throw "$fileName points to a missing file: $secretPath"
        }
        $value = (Get-Content -Raw -LiteralPath $secretPath).Trim()
    } else {
        Assert-EnvValue $Values $Name
        $value = [string]$Values[$Name]
    }

    $knownUnsafe = @(
        "replace-with-a-strong-password",
        "replace-with-a-different-strong-password",
        "replace-with-a-strong-grafana-password",
        "city_dev_password",
        "ci-postgres-password",
        "ci-redis-password",
        "smoke-postgres-password",
        "smoke-redis-password",
        "smoke-grafana-password",
        "drill-postgres-password",
        "drill-redis-password",
        "drill-grafana-password"
    )

    if ($knownUnsafe -contains $value -or $value -like "replace-with-*") {
        throw "$Name still uses a template/test value."
    }
    if ($value.Length -lt 16) {
        throw "$Name must be at least 16 characters."
    }
}

function Resolve-SecretPath {
    param([Parameter(Mandatory = $true)][string]$Path)

    if ([System.IO.Path]::IsPathRooted($Path)) {
        return $Path
    }

    $envDirectory = Split-Path -Parent $envPath.Path
    return Join-Path $envDirectory $Path
}

function Assert-SecretReference {
    param(
        [Parameter(Mandatory = $true)][hashtable]$Values,
        [Parameter(Mandatory = $true)][string]$Name
    )

    if ($Values.ContainsKey($Name) -and -not [string]::IsNullOrWhiteSpace($Values[$Name])) {
        return
    }

    $fileName = "${Name}_FILE"
    if ($Values.ContainsKey($fileName) -and -not [string]::IsNullOrWhiteSpace($Values[$fileName])) {
        $secretPath = Resolve-SecretPath $Values[$fileName]
        if (-not (Test-Path -LiteralPath $secretPath)) {
            throw "$fileName points to a missing file: $secretPath"
        }
        return
    }

    throw "$Name or $fileName is required in $EnvFile."
}

function Assert-ProductionCors {
    param([Parameter(Mandatory = $true)][hashtable]$Values)

    Assert-EnvValue $Values "CITY_CORS_ORIGINS"
    $origins = [string]$Values["CITY_CORS_ORIGINS"]
    if ($origins -eq "*") {
        throw "CITY_CORS_ORIGINS must not be wildcard in production."
    }

    foreach ($origin in $origins.Split(",", [System.StringSplitOptions]::RemoveEmptyEntries)) {
        $trimmed = $origin.Trim()
        if (-not $trimmed.StartsWith("https://")) {
            throw "CITY_CORS_ORIGINS entries must use https:// in production: $trimmed"
        }
    }
}

function Assert-ReleaseMetadata {
    param(
        [Parameter(Mandatory = $true)][hashtable]$Values,
        [Parameter(Mandatory = $true)][bool]$AllowPlaceholders
    )

    foreach ($name in @("CITY_RELEASE_SHA", "CITY_RELEASE_IMAGE", "CITY_RELEASE_VERSION")) {
        Assert-EnvValue $Values $name
        $value = [string]$Values[$name]
        if (-not $AllowPlaceholders -and ($value -like "replace-with-*" -or $value -in @("dev", "local", "unknown"))) {
            throw "$name must identify the immutable release artifact."
        }
    }
}

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][scriptblock]$Command
    )

    Write-Host "== $Name =="
    & $Command
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

$envPath = Resolve-Path -LiteralPath $EnvFile -ErrorAction SilentlyContinue
if (-not $envPath) {
    throw "Production env file '$EnvFile' was not found."
}

if (-not $AllowExampleEnv -and $envPath.Path.EndsWith(".example", [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to preflight an example env file. Pass -AllowExampleEnv only for local validation."
}

$envValues = Read-DotEnv $envPath.Path
if (-not $AllowExampleEnv) {
    Assert-StrongSecret $envValues "POSTGRES_PASSWORD"
    Assert-StrongSecret $envValues "REDIS_PASSWORD"
    Assert-StrongSecret $envValues "GRAFANA_ADMIN_PASSWORD"
} else {
    Assert-SecretReference $envValues "POSTGRES_PASSWORD"
    Assert-SecretReference $envValues "REDIS_PASSWORD"
    Assert-SecretReference $envValues "GRAFANA_ADMIN_PASSWORD"
}
Assert-SecretReference $envValues "CITY_DATABASE_URL"
Assert-SecretReference $envValues "REDIS_URL"
Assert-ProductionCors $envValues
Assert-ReleaseMetadata $envValues $AllowExampleEnv.IsPresent

if ($envValues.ContainsKey("CITY_RUN_MIGRATIONS_ON_STARTUP") -and $envValues["CITY_RUN_MIGRATIONS_ON_STARTUP"] -ne "false") {
    throw "CITY_RUN_MIGRATIONS_ON_STARTUP must remain false in production."
}

Invoke-Step "Targeted production gate" {
    & "$root\scripts\pwsh7.ps1" -NoProfile -File "$root\scripts\check_targeted.ps1" prod-fast
}

Invoke-Step "Production Compose config with requested env" {
    docker compose --env-file $envPath.Path -f docker-compose.prod.yml config --quiet
}

if (-not $SkipBackupDrill) {
    Invoke-Step "Backup restore drill" {
        & "$root\scripts\pwsh7.ps1" -NoProfile -File "$root\scripts\drill_backup_restore.ps1" `
            -ProjectName "$ProjectName-backup"
    }
}

if (-not $SkipSmoke) {
    Invoke-Step "Isolated production smoke" {
        & "$root\scripts\pwsh7.ps1" -NoProfile -File "$root\scripts\smoke_production.ps1" `
            -ProjectName "$ProjectName-smoke"
    }
}

Write-Host "Rollout preflight passed."

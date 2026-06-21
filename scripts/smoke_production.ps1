param(
    [int]$Port = 8001,
    [string]$ProjectName = "ces-prod-smoke"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$secretDir = Join-Path $root ".cache\prod-smoke-secrets"
New-Item -ItemType Directory -Force -Path $secretDir | Out-Null
$postgresPasswordFile = Join-Path $secretDir "postgres_password.txt"
$redisPasswordFile = Join-Path $secretDir "redis_password.txt"
$grafanaPasswordFile = Join-Path $secretDir "grafana_admin_password.txt"
$databaseUrlFile = Join-Path $secretDir "city_database_url.txt"
$redisUrlFile = Join-Path $secretDir "redis_url.txt"

$postgresPassword = "smokeLocalPostgresSecret2026!"
$redisPassword = "smokeLocalRedisSecret2026!"
$grafanaPassword = "smokeLocalGrafanaSecret2026!"
Set-Content -NoNewline -Encoding UTF8 -Path $postgresPasswordFile -Value $postgresPassword
Set-Content -NoNewline -Encoding UTF8 -Path $redisPasswordFile -Value $redisPassword
Set-Content -NoNewline -Encoding UTF8 -Path $grafanaPasswordFile -Value $grafanaPassword
Set-Content -NoNewline -Encoding UTF8 -Path $databaseUrlFile -Value "postgresql+psycopg2://city:$postgresPassword@postgres:5432/city_game"
Set-Content -NoNewline -Encoding UTF8 -Path $redisUrlFile -Value "redis://:$redisPassword@redis:6379/0"

$env:POSTGRES_PASSWORD_FILE = $postgresPasswordFile
$env:REDIS_PASSWORD_FILE = $redisPasswordFile
$env:CITY_DATABASE_URL_FILE = $databaseUrlFile
$env:REDIS_URL_FILE = $redisUrlFile
$env:CITY_CORS_ORIGINS = "https://smoke.example"
$env:CITY_RELEASE_SHA = "smoke-release-sha"
$env:CITY_RELEASE_IMAGE = "ces-backend:smoke"
$env:CITY_RELEASE_VERSION = "0.3.0-smoke"
$env:BACKEND_PORT = $Port.ToString()
$env:PROMETHEUS_PORT = ($Port + 90).ToString()
$env:GRAFANA_PORT = ($Port + 91).ToString()
$env:GRAFANA_ADMIN_USER = "admin"
$env:GRAFANA_ADMIN_PASSWORD_FILE = $grafanaPasswordFile

$composeArgs = @(
    "--project-name", $ProjectName,
    "-f", "docker-compose.prod.yml"
)

try {
    Write-Host "== Build and start production stack =="
    docker compose @composeArgs up -d --build --wait
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    Write-Host "== Release image labels =="
    $releaseLabels = docker image inspect $env:CITY_RELEASE_IMAGE `
        --format "{{ index .Config.Labels `"org.opencontainers.image.revision`" }}|{{ index .Config.Labels `"org.opencontainers.image.ref.name`" }}|{{ index .Config.Labels `"org.opencontainers.image.version`" }}"
    if ($LASTEXITCODE -ne 0) {
        throw "Could not inspect release image '$env:CITY_RELEASE_IMAGE'."
    }
    $releaseLabelParts = $releaseLabels.Split("|")
    if ($releaseLabelParts.Count -ne 3) {
        throw "Release image labels were not readable."
    }
    if ($releaseLabelParts[0] -ne $env:CITY_RELEASE_SHA) {
        throw "Release image revision label '$($releaseLabelParts[0])' did not match expected '$env:CITY_RELEASE_SHA'."
    }
    if ($releaseLabelParts[1] -ne $env:CITY_RELEASE_IMAGE) {
        throw "Release image ref label '$($releaseLabelParts[1])' did not match expected '$env:CITY_RELEASE_IMAGE'."
    }
    if ($releaseLabelParts[2] -ne $env:CITY_RELEASE_VERSION) {
        throw "Release image version label '$($releaseLabelParts[2])' did not match expected '$env:CITY_RELEASE_VERSION'."
    }

    Write-Host "== Migration job =="
    $migrateContainerId = docker compose @composeArgs ps --all -q migrate
    if ($LASTEXITCODE -ne 0 -or -not $migrateContainerId) {
        throw "Production migration job container was not found."
    }
    $migrateExitCode = docker inspect $migrateContainerId --format "{{.State.ExitCode}}"
    if ($LASTEXITCODE -ne 0 -or $migrateExitCode -ne "0") {
        docker compose @composeArgs logs migrate
        throw "Production migration job exited with code $migrateExitCode."
    }

    $baseUrl = "http://127.0.0.1:$Port"

    Write-Host "== Readiness =="
    $ready = Invoke-RestMethod -Uri "$baseUrl/health/ready"
    if ($ready.status -ne "ready") {
        throw "Production readiness returned '$($ready.status)'."
    }
    if ($ready.release.sha -ne $env:CITY_RELEASE_SHA) {
        throw "Readiness release sha '$($ready.release.sha)' did not match expected '$env:CITY_RELEASE_SHA'."
    }
    if (-not $ready.schema_version) {
        throw "Readiness did not expose schema_version."
    }

    Write-Host "== Metrics =="
    $metrics = Invoke-RestMethod -Uri "$baseUrl/metrics"
    if (
        $metrics -notmatch "ces_http_requests_total" -or
        $metrics -notmatch "ces_http_request_duration_seconds"
    ) {
        throw "Expected CES Prometheus metrics were not exposed."
    }

    Write-Host "== Prometheus scrape =="
    $prometheusBaseUrl = "http://127.0.0.1:$env:PROMETHEUS_PORT"
    Invoke-RestMethod -Uri "$prometheusBaseUrl/-/healthy" | Out-Null
    $upQuery = $null
    $scrapeDeadline = (Get-Date).AddSeconds(60)
    do {
        $upQuery = Invoke-RestMethod -Uri "$prometheusBaseUrl/api/v1/query?query=up%7Bjob%3D%22ces-backend%22%7D"
        if (
            $upQuery.status -eq "success" -and
            $upQuery.data.result.Count -ge 1 -and
            $upQuery.data.result[0].value[1] -eq "1"
        ) {
            break
        }
        Start-Sleep -Seconds 3
    } while ((Get-Date) -lt $scrapeDeadline)

    if (
        $upQuery.status -ne "success" -or
        $upQuery.data.result.Count -lt 1 -or
        $upQuery.data.result[0].value[1] -ne "1"
    ) {
        throw "Prometheus did not report ces-backend as an up scrape target."
    }
    $metricQuery = Invoke-RestMethod -Uri "$prometheusBaseUrl/api/v1/query?query=ces_http_requests_total"
    if ($metricQuery.status -ne "success") {
        throw "Prometheus query for CES metrics failed."
    }

    Write-Host "== Grafana health =="
    $grafanaHealth = Invoke-RestMethod -Uri "http://127.0.0.1:$env:GRAFANA_PORT/api/health"
    if ($grafanaHealth.database -ne "ok") {
        throw "Grafana health database status is '$($grafanaHealth.database)'."
    }

    Write-Host "== Production-only route policy =="
    foreach ($path in @("/docs", "/api/frozen/sports/clubs")) {
        try {
            Invoke-WebRequest -Uri "$baseUrl$path" -UseBasicParsing | Out-Null
            throw "Expected $path to return 404 in production."
        }
        catch {
            if ($_.Exception.Response.StatusCode.value__ -ne 404) {
                throw
            }
        }
    }

    Write-Host "Production smoke passed."
}
finally {
    Write-Host "== Remove production smoke stack =="
    docker compose @composeArgs down --volumes --remove-orphans
}

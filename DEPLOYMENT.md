# Deployment Guide for City Economic Simulator

## Prerequisites

- Docker and Docker Compose installed
- Git repository cloned locally

## Environment Setup

1. Copy the production environment template:
```bash
cp .env.production.example .env.production
```

2. Create production secret files from the examples:
```bash
mkdir -p secrets
cp secrets/postgres_password.example.txt secrets/postgres_password.txt
cp secrets/redis_password.example.txt secrets/redis_password.txt
cp secrets/grafana_admin_password.example.txt secrets/grafana_admin_password.txt
cp secrets/city_database_url.example.txt secrets/city_database_url.txt
cp secrets/redis_url.example.txt secrets/redis_url.txt
chmod 600 secrets/*.txt
```

3. Update the secret files and `.env.production`:
   - Put secure values in `secrets/postgres_password.txt`, `secrets/redis_password.txt`, and `secrets/grafana_admin_password.txt`
   - Put the full SQLAlchemy URL in `secrets/city_database_url.txt`
   - Put the full Redis URL in `secrets/redis_url.txt`
   - Keep `.env.production` on `_FILE` variables that point to these files
   - Set `CITY_CORS_ORIGINS` to the HTTPS origin of the client
   - Set `CITY_RELEASE_SHA`, `CITY_RELEASE_IMAGE`, and `CITY_RELEASE_VERSION` to the immutable artifact being deployed
   - Keep the scheduler renew interval below its lease TTL
   - Keep `CITY_LOG_FORMAT=json` for container-friendly production logs
   - Keep `CITY_RUN_MIGRATIONS_ON_STARTUP=false`; production migrations run in the one-shot `migrate` service
   - Keep `.env.production` uncommitted and restrict local permissions, for example `chmod 600 .env.production` on Linux hosts

## Production Deployment

1. Build or publish the backend image:

- GitHub Actions workflow `.github/workflows/release-image.yml` builds the backend Docker image.
- On `main`/`master` or manual runs, it publishes `ghcr.io/<owner>/<repo>/ces-backend:<git-sha>` and uploads a `release.env` artifact.
- Copy the artifact values into `.env.production`:
```bash
CITY_RELEASE_SHA=<git-sha>
CITY_RELEASE_IMAGE=ghcr.io/<owner>/<repo>/ces-backend:<git-sha>
CITY_RELEASE_VERSION=0.3.0
```

`docker-compose.prod.yml` tags both `backend` and `migrate` with `CITY_RELEASE_IMAGE`, and the Docker image carries matching OCI release labels.

2. Run rollout preflight:
```powershell
.\scripts\pwsh7.ps1 -NoProfile -File .\scripts\rollout_preflight.ps1 -EnvFile .\.env.production
```

This checks production env hardening, targeted production tests, Compose config, backup/restore drill, and an isolated production smoke stack.

GitHub Actions also has `.github/workflows/production-smoke.yml` for the isolated production stack. It can be run manually, runs weekly, and triggers on deploy-related path changes in PRs or pushes to the mainline branches.

3. Start services from the immutable image:
```bash
docker compose --env-file .env.production -f docker-compose.prod.yml pull backend migrate
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --no-build --wait
```

The production Compose stack runs `migrate` once before `backend` starts. If migrations fail, the backend service does not start.

4. Verify deployment:
```bash
curl http://localhost:8000/health
curl --fail http://localhost:8000/health/ready
```

5. Check service state:
```bash
docker compose --env-file .env.production -f docker-compose.prod.yml ps
docker compose --env-file .env.production -f docker-compose.prod.yml logs --tail=100 backend
```

## Staging or Remote Host Runbook

Use this flow when the backend image was published by `.github/workflows/release-image.yml` and the host should not build application code locally.

1. Prepare the host:
```bash
mkdir -p /opt/ces/secrets
cd /opt/ces
```

2. Copy these files from the repository or deployment bundle:
```text
.env.production
docker-compose.prod.yml
deploy/prometheus/prometheus.yml
deploy/grafana/provisioning/
deploy/grafana/dashboards/
secrets/*.txt
```

3. Authenticate Docker to the registry:
```bash
echo "<github-token-with-package-read>" | docker login ghcr.io -u <github-user> --password-stdin
```

4. Apply the `release.env` artifact values to `.env.production`:
```bash
CITY_RELEASE_SHA=<git-sha>
CITY_RELEASE_IMAGE=ghcr.io/<owner>/<repo>/ces-backend:<git-sha>
CITY_RELEASE_VERSION=0.3.0
```

5. Validate and start without local builds:
```bash
docker compose --env-file .env.production -f docker-compose.prod.yml config --quiet
docker compose --env-file .env.production -f docker-compose.prod.yml pull backend migrate
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --no-build --wait
curl --fail http://localhost:8000/health/ready
```

6. Confirm runtime identity:
```bash
curl --fail http://localhost:8000/health/ready
set -a; . ./.env.production; set +a
docker image inspect "$CITY_RELEASE_IMAGE" --format '{{ index .Config.Labels "org.opencontainers.image.revision" }}'
```

The readiness `release.sha`, `release.image`, and `release.version` must match `.env.production`; the Docker label revision must match `CITY_RELEASE_SHA`.

## Rollback Strategy

Prefer roll-forward fixes for application bugs after migrations have been applied. Use rollback only when the new containers fail readiness or the migration has not changed irreversible data.

### Before rollout
- Run `scripts/rollout_preflight.ps1`.
- Keep the generated logical backup from `scripts/drill_backup_restore.ps1` or create a fresh external `pg_dump`.
- Record the current Git SHA, image tag, `CITY_RELEASE_*` values, and `alembic_version`.

### Container rollback
```bash
CITY_RELEASE_SHA=<previous-good-sha>
CITY_RELEASE_IMAGE=ghcr.io/<owner>/<repo>/ces-backend:<previous-good-sha>
CITY_RELEASE_VERSION=<previous-good-version>
docker compose --env-file .env.production -f docker-compose.prod.yml pull backend migrate
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --no-build --wait
curl --fail http://localhost:8000/health/ready
```

Verify that readiness reports the expected release and schema:
```bash
curl --fail http://localhost:8000/health/ready
```
The response must include the expected `release.sha`, `release.image`, `release.version`, and `schema_version`.

### Database rollback
Only use Alembic downgrade when the target migration is explicitly reversible and no production writes depend on the new shape:
```bash
docker compose --env-file .env.production -f docker-compose.prod.yml run --rm backend alembic downgrade -1
```

For destructive or uncertain migration failures, restore the validated logical backup into a fresh database/volume and repoint `CITY_DATABASE_URL_FILE` to a secret file containing the restored database URL instead of editing live data in place.

## Development Setup

1. Start the development stack:
```bash
docker compose up
```

2. Hot-reload is enabled for backend code changes.

## Service URLs

- Backend API: http://localhost:8000
- Health Check: http://localhost:8000/health
- API Docs: http://localhost:8000/docs
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001
- PostgreSQL and Redis are internal-only in production.
- Prometheus and Grafana bind to `127.0.0.1` by default; expose them only through VPN, SSO, or a locked-down reverse proxy.

## Common Commands

### View logs
```bash
# All services
docker compose --env-file .env.production -f docker-compose.prod.yml logs -f

# Specific service
docker compose --env-file .env.production -f docker-compose.prod.yml logs -f backend
```

### Stop services
```bash
docker compose --env-file .env.production -f docker-compose.prod.yml down
```

### Update and restart
```bash
docker compose --env-file .env.production -f docker-compose.prod.yml pull
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build --force-recreate --wait
```

### Database operations
```bash
# Run production migrations explicitly
docker compose --env-file .env.production -f docker-compose.prod.yml run --rm migrate

# Create new migration
docker compose --env-file .env.production -f docker-compose.prod.yml run --rm backend alembic revision --autogenerate -m "description"

# Apply migrations
docker compose --env-file .env.production -f docker-compose.prod.yml run --rm migrate

# Downgrade (if needed)
docker compose --env-file .env.production -f docker-compose.prod.yml run --rm backend alembic downgrade -1
```

### Backup restore drill
Run the isolated drill before risky migration or deployment work:
```powershell
.\scripts\pwsh7.ps1 -NoProfile -File .\scripts\drill_backup_restore.ps1
```

The drill starts a separate Compose project, applies migrations, seeds sentinel restore-validation rows, creates a PostgreSQL dump, restores it into a validation database, checks `alembic_version`, checks `city_economy_snapshots`, compares key table row counts, verifies sentinel money-supply data, and then removes the temporary stack.

Validate an existing logical backup without creating a new dump:
```powershell
.\scripts\pwsh7.ps1 -NoProfile -File .\scripts\drill_backup_restore.ps1 -ValidateExistingBackup -BackupPath .\backups\prod.sql -ExpectedRowCounts "alembic_version=1,cities=5,city_metrics=5,city_economy_snapshots=120"
```

`-ExpectedRowCounts` is optional and accepts comma-separated `table=count` checks for tracked restore tables. Use it when production row counts are known from a pre-deploy snapshot.

## Monitoring

### Health Checks
- `/health` - Overall service health
- `/health/ready` - Service readiness
- `/health/live` - Process liveness
- `/health` and `/health/ready` include release metadata and the current Alembic schema version for rollout verification.
- `/metrics` - Prometheus-compatible request counters and latency histograms

### Prometheus and Grafana
- Prometheus scrapes `backend:8000/metrics` as job `ces-backend`.
- Grafana provisions the `CES Prometheus` datasource and the `CES Overview` dashboard automatically.
- Verify scrape status:
```bash
curl "http://localhost:9090/api/v1/query?query=up%7Bjob%3D%22ces-backend%22%7D"
```
- Verify Grafana:
```bash
curl http://localhost:3001/api/health
```

### Logs Location
- Application logs: container stdout/stderr via `docker compose logs`
- PostgreSQL logs: Docker logs for postgres container
- HTTP responses include `X-Request-ID`; backend logs include the same `request_id`.

### Scheduler leadership
- Multiple backend replicas are supported.
- One replica owns a renewable Redis lease and runs scheduled economy ticks.
- PostgreSQL advisory transaction locks prevent the same city from being ticked concurrently.
- If Redis is unavailable, scheduled ticks fail closed until leadership can be acquired again.
- Defaults: lease TTL `60s`, renew every `15s`, follower retry every `5s`.

## Troubleshooting

### Service won't start
1. Check environment variables in `.env.production`
2. Verify ports aren't already in use
3. Check Docker logs: `docker compose logs [service]`

### Database connection issues
1. Ensure PostgreSQL is healthy: `docker compose ps postgres`
2. Check `CITY_DATABASE_URL_FILE` in `.env.production` and the referenced secret file
3. Verify migrations are applied

### Redis connection issues
1. Check Redis is healthy: `docker compose ps redis`
2. Verify Redis URL in environment
3. Check Redis password matches

## Security Notes

- Change default passwords before production
- Use HTTPS in production (add Nginx reverse proxy)
- Do not expose Prometheus or Grafana directly to the public internet; they bind to localhost by default and should stay behind VPN, SSO, or a locked-down reverse proxy.
- Never commit `.env.production`; rotate any value that may have been exposed in logs, screenshots, or commits.
- Prefer host/CI secret stores over flat files for managed deployments.
- Regularly update Docker images

## Backup and Recovery

### Database Backup
```bash
docker compose exec postgres pg_dump -U city city_game > backup.sql
```

### Database Restore
```bash
docker compose exec -T postgres psql -U city city_game < backup.sql
```

### Volume Backup
```bash
docker run --rm -v ces_postgres_data:/data -v $(pwd):/backup ubuntu tar cvf /backup/postgres_backup.tar /data
```

### Restore Drill Policy

- Run `scripts/drill_backup_restore.ps1` before production migrations with data-shape risk.
- Keep at least one recent logical `pg_dump` outside the Docker host before running irreversible migrations.
- Treat a backup as valid only after a restore into a separate database succeeds and key table row counts match.
- For external or manually copied backups, use `-ValidateExistingBackup` before relying on the dump for rollback.

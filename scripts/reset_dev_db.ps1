# Reset local development database. This destroys local dev data.
# Usage: .\scripts\reset_dev_db.ps1

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

$env:PGPASSWORD = "city_dev_password"
$env:CITY_DATABASE_URL = "postgresql+psycopg2://city:city_dev_password@127.0.0.1:5432/city_game"

$psql = "C:\Program Files\PostgreSQL\16\bin\psql.exe"
$python = if (Test-Path ".\.venv\Scripts\python.exe") { ".\.venv\Scripts\python.exe" } else { "python" }

Write-Host "Resetting city_game public schema..."
& $psql -U city -h 127.0.0.1 -p 5432 -d city_game -c "DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO city;"

Write-Host "Applying migrations..."
& $python -m alembic upgrade head

Write-Host "Seeding starter city..."
& $python -c "from backend.app.database import SessionLocal; from backend.app.seed import seed_initial_data; db=SessionLocal(); seed_initial_data(db); db.close()"

Write-Host "Dev database reset complete."

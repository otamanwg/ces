# Task runner для City Economic Simulator
# Використання: just <task>
# Приклад: just test

set shell := ["C:/Tools/PowerShell/7.6.2/pwsh.exe", "-c"]

# Запуск backend в режимі розробки
run:
    .venv/Scripts/python.exe -m uvicorn backend.main:app --reload --port 8000

# Запуск усіх тестів backend
test:
    .venv/Scripts/python.exe -m pytest backend/tests -q

# Запуск тестів із verbose output
test-verbose:
    .venv/Scripts/python.exe -m pytest backend/tests -v --tb=short

# Форматування Python коду (ruff — заміна black)
format-python:
    .venv/Scripts/python.exe -m ruff format backend/app backend/main.py

# Форматування C# коду (Godot client)
format-csharp:
    C:\tools\dotnet-sdk\dotnet.exe format client/city_economic_simulator.csproj

# Форматування всього коду
format: format-python format-csharp

# Збірка Godot C# проєкту
build-client:
    C:\tools\dotnet-sdk\dotnet.exe build client/city_economic_simulator.csproj

# Перевірка стилю Python (ruff lint + format check)
check-python:
    .venv/Scripts/python.exe -m ruff check backend/app backend/main.py
    .venv/Scripts/python.exe -m ruff format --check backend/app backend/main.py

# Міграції бази даних (upgrade)
migrate:
    .venv/Scripts/python.exe -m alembic upgrade head

# Створення нової міграції (потребує аргумент msg)
migrate-create msg:
    .venv/Scripts/python.exe -m alembic revision --autogenerate -m "{{msg}}"

# Генерація C# DTO з OpenAPI (потребує запущеного backend на :8000)
generate-api-client:
    $env:Path = "C:\Users\agga\.dotnet\tools;C:\ces\.tools\node;" + $env:Path
    nswag openapi2csclient /input:http://127.0.0.1:8000/openapi.json /output:client/scripts/generated/CityApiModels.cs /namespace:City.Api /classname:CityApiClient /generateClientClasses:false /generateDtoTypes:true /jsonLibrary:SystemTextJson

# Запуск Godot MCP bridge
mcp-bridge:
    .venv/Scripts/python.exe scripts/godot_mcp_bridge.py

# Статус Godot MCP bridge
mcp-status:
    Invoke-RestMethod -Uri "http://127.0.0.1:6507/status" -Method Get | ConvertTo-Json

# Перевірка локального середовища розробки
doctor:
    ./scripts/pwsh7.ps1 -NoProfile -File ./scripts/doctor.ps1

# Повний локальний quality gate
check:
    ./scripts/pwsh7.ps1 -NoProfile -File ./scripts/check.ps1

# Список targeted quality gates
check-targets:
    ./scripts/pwsh7.ps1 -NoProfile -File ./scripts/check_targeted.ps1 list

# Швидкі targeted gates для конкретних slices
check-target profile:
    ./scripts/pwsh7.ps1 -NoProfile -File ./scripts/check_targeted.ps1 {{profile}}

check-backend-fast:
    ./scripts/pwsh7.ps1 -NoProfile -File ./scripts/check_targeted.ps1 backend-fast

check-auth:
    ./scripts/pwsh7.ps1 -NoProfile -File ./scripts/check_targeted.ps1 auth

check-economy:
    ./scripts/pwsh7.ps1 -NoProfile -File ./scripts/check_targeted.ps1 economy

check-buildings:
    ./scripts/pwsh7.ps1 -NoProfile -File ./scripts/check_targeted.ps1 buildings

check-scheduler:
    ./scripts/pwsh7.ps1 -NoProfile -File ./scripts/check_targeted.ps1 scheduler

check-observability:
    ./scripts/pwsh7.ps1 -NoProfile -File ./scripts/check_targeted.ps1 observability

check-districts:
    ./scripts/pwsh7.ps1 -NoProfile -File ./scripts/check_targeted.ps1 districts

check-npcs:
    ./scripts/pwsh7.ps1 -NoProfile -File ./scripts/check_targeted.ps1 npcs

check-prod:
    ./scripts/pwsh7.ps1 -NoProfile -File ./scripts/check_targeted.ps1 prod-fast

check-prod-smoke:
    ./scripts/pwsh7.ps1 -NoProfile -File ./scripts/check_targeted.ps1 prod-smoke

check-client:
    ./scripts/pwsh7.ps1 -NoProfile -File ./scripts/check_targeted.ps1 client

check-client-smoke:
    ./scripts/pwsh7.ps1 -NoProfile -File ./scripts/check_targeted.ps1 client-smoke

# Перевірка tracked-файлів на випадково додані секрети
secret-scan:
    .venv/Scripts/python.exe scripts/check_secrets.py

# API smoke проти запущеного backend
smoke-api:
    .venv/Scripts/python.exe scripts/smoke_mvp.py

# Ізольований smoke production Compose stack
smoke-production:
    ./scripts/pwsh7.ps1 -NoProfile -File ./scripts/smoke_production.ps1

# Godot dashboard smoke через MCP bridge
smoke-godot:
    ./scripts/pwsh7.ps1 -NoProfile -File ./scripts/smoke_godot_dashboard.ps1

# Headless Godot smoke для API dispatch recovery
smoke-client-api:
    ./scripts/pwsh7.ps1 -NoProfile -File ./scripts/smoke_client_api_dispatch.ps1

# Лінтинг Python (ruff)
lint-python:
    .venv/Scripts/python.exe -m ruff check backend/app backend/main.py

# Автофікс лінтинг-помилок Python
lint-fix-python:
    .venv/Scripts/python.exe -m ruff check --fix backend/app backend/main.py

# Статичний аналіз типів Python (pyright)
typecheck-python:
    .venv/Scripts/python.exe -m pyright backend/app backend/main.py

# Очистка кешів Python
clean:
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue backend/app/__pycache__, backend/tests/__pycache__
    Write-Host "Кеш очищено."

# Запуск PostgreSQL через Docker
postgres-up:
    docker compose up -d postgres

# Зупинка PostgreSQL
postgres-down:
    docker compose down

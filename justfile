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

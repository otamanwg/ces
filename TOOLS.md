# Інструменти розробника — City Economic Simulator

Документ для AI-асистентів та розробників. Описує весь стек, шляхи до інструментів і як ними користуватися.

## Операційна система

- **OS:** Windows (x64)
- **Shell:** PowerShell 7.6.2 (`C:\tools\PowerShell\7.6.2\pwsh.exe`)
- **Git:** MinGit (`C:\Tools\MinGit\cmd\git.exe`)

## Python backend

- **Python:** 3.13 (venv у `.venv/`)
- **Package manager:** `uv` (`C:\Users\agga\.local\bin\uv.exe`)
- **Task runner:** `just` (`C:\tools\just\just.exe`)
- **Framework:** FastAPI 0.100+ + SQLAlchemy 2.0+ + Pydantic 2.0+
- **DB:** PostgreSQL 16 (Docker container `city-economic-simulator-postgres`)
- **Migrations:** Alembic
- **Tests:** pytest (90 тестів, всі проходять)
- **Type checker:** pyright (налаштований у `pyproject.toml`)

### Залежності керуються через `pyproject.toml`

```bash
# Синхронізація залежностей
uv sync --all-extras

# Встановлення dev-залежностей
uv pip install -e ".[dev]"
```

### Запуск backend

```bash
just run           # uvicorn --reload --port 8000
just test          # pytest backend/tests -q
just test-verbose  # pytest backend/tests -v --tb=short
```

### Форматування та лінтинг

```bash
just format-python     # ruff format backend/app backend/main.py
just lint-python       # ruff check backend/app backend/main.py
just lint-fix-python   # ruff check --fix backend/app backend/main.py
just check-python      # ruff check + ruff format --check
```

### База даних

```bash
just postgres-up   # docker compose up -d postgres
just postgres-down # docker compose down
just migrate       # alembic upgrade head
```

## Godot Client (C#)

- **Godot Engine:** 4.3-stable .NET edition (`C:\tools\Godot\Godot_v4.3-stable_mono_win64\`)
- **.NET SDK:** 8.0.421 (`C:\tools\dotnet-sdk\`)
- **Target framework:** net8.0
- **Project file:** `client/city_economic_simulator.csproj`
- **Main scene:** `client/scenes/city_dashboard.tscn`

### Запуск

```bash
just build-client    # dotnet build client/city_economic_simulator.csproj
just format-csharp   # dotnet format client/city_economic_simulator.csproj
```

## Godot MCP Bridge

- **Bridge script:** `scripts/godot_mcp_bridge.py`
- **WebSocket:** `ws://127.0.0.1:6505` (Godot ↔ Bridge)
- **HTTP Control:** `http://127.0.0.1:6507` (AI ↔ Bridge)
- **Status endpoint:** `http://127.0.0.1:6507/status`
- **Invoke endpoint:** `POST http://127.0.0.1:6507/invoke`

### Запуск

```bash
just mcp-bridge   # python scripts/godot_mcp_bridge.py
just mcp-status   # перевірка статусу
```

### Доступні MCP tools

- `get_project_settings` — налаштування проєкту
- `get_console_log` — логи Godot
- `get_errors` — помилки компіляції
- `scene_tree_dump` — дерево сцен
- `file_tools` — робота з файлами
- `script_tools` — робота зі скриптами
- `project_tools` — конфігурація проєкту
- `visualizer_tools` — візуальні інструменти

## Pre-commit hooks

- **Config:** `.pre-commit-config.yaml`
- **Hooks:**
  - `trailing-whitespace`, `end-of-file-fixer`, `check-yaml`
  - `ruff` — lint + autofix
  - `ruff-format` — форматування Python
  - `dotnet-format` — форматування C#

```bash
# Встановлення hooks
python -m pre_commit install

# Запуск на всіх файлах
python -m pre_commit run --all-files
```

## CI/CD (GitHub Actions)

- **Config:** `.github/workflows/ci.yml`
- **Jobs:**
  - Backend tests (pytest) з PostgreSQL сервісом
  - Godot C# build (dotnet build)

## Архітектура backend

```
backend/
  app/
    api/routes/      # FastAPI endpoints
    core/            # Config, exceptions
    database.py      # DB session
    models.py        # SQLAlchemy ORM models
    repositories/    # Repository layer (NEW)
    schemas/         # Pydantic DTOs
    services/        # Business logic
    realtime/        # WebSocket manager
    seed.py          # Initial data
  main.py            # FastAPI app entrypoint
  alembic/           # Migrations
  tests/             # pytest tests (90 passed)
```

## Repository layer

- `BaseRepository[T]` — базовий CRUD
- `PlayerRepository` — гравці + auth
- `CityRepository` — міста
- `BusinessRepository` — бізнеси
- `JobRepository` — вакансії
- `HostelRepository` — житло
- `LandParcelRepository` — земельні ділянки

## Структура проєкту

```
ces/
  backend/           # Python FastAPI
  client/            # Godot 4.3 C#
  database/          # SQL init scripts
  scripts/           # Godot MCP bridge
  docs/              # Documentation
  justfile           # Task runner
  pyproject.toml     # Python dependencies
  docker-compose.yml # PostgreSQL
  .pre-commit-config.yaml
  .env.example
```

## Змінні оточення (з .env)

```
CITY_DATABASE_URL=postgresql+psycopg2://city:city_dev_password@127.0.0.1:5432/city_game
CITY_TEST_DATABASE_URL=postgresql+psycopg2://city:city_dev_password@127.0.0.1:5432/city_game_test
CITY_CORS_ORIGINS=*
CITY_DEBUG=true
```

## Що ще можна додати

- `pyright` — статичний аналіз типів Python
- OpenAPI → C# code generator — type-safe API клієнт
- `structlog` — структуроване логування
- GitHub Actions: Godot build + test CI

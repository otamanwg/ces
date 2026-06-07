# Інструменти розробника — City Economic Simulator

> **⚠️ ПРАВИЛО ДЛЯ AI-АСИСТЕНТА (Cascade/Windsurf):**
> Перед кожним завданням перевір цей файл. Використовуй наявні інструменти активно:
> - Godot MCP Bridge → перевіряй помилки сцен після змін C#
> - Playwright MCP → smoke test API та UI локально
> - Context7 MCP → актуальні доки FastAPI/SQLAlchemy/APScheduler
> - `scripts/smoke_mvp.py` → перевірка backend після змін
> - `scripts/capture_dashboard.ps1` → скриншот для visual QA
> Не покладайся тільки на `check.ps1` — він не замінює smoke тестів.

---

## Операційна система

- **OS:** Windows x64
- **Shell:** PowerShell 7.6.2 → `C:\Tools\PowerShell\7.6.2\pwsh.exe`
- **Git:** MinGit → `C:\Tools\MinGit\cmd\git.exe`

## Інвентар C:\Tools (всі встановлені інструменти)

| Інструмент | Версія | Шлях | Використання |
|------------|--------|------|--------------|
| PowerShell | 7.6.2 | `C:\Tools\PowerShell\7.6.2\pwsh.exe` | Shell для всіх скриптів |
| .NET SDK | 8.0.421 | `C:\Tools\dotnet-sdk\dotnet.exe` | Godot C# build |
| .NET runtime | legacy | `C:\Tools\dotnet\` | Не використовувати — тільки dotnet-sdk |
| Godot | 4.3-stable mono | `C:\Tools\Godot\Godot_v4.3-stable_mono_win64\` | Ігровий рушій |
| Godot | 4.2.2-stable mono | `C:\Tools\Godot\Godot_v4.2.2-stable_mono_win64\` | Запасна версія |
| MinGit | latest | `C:\Tools\MinGit\cmd\git.exe` | Git операції |
| just | latest | `C:\Tools\just\just.exe` | Task runner |
| Node.js | 22.16.0 | `C:\Tools\nodejs\node.exe` | MCP servers, npx |
| npm | 10.9.2 | `C:\Tools\nodejs\npm.cmd` | Node пакети |
| npx | 10.9.2 | `C:\Tools\nodejs\npx.cmd` | Запуск MCP servers |
| Blender | latest | `C:\Tools\Blender\` | 3D аватари (anime pipeline) |
| Rufus | latest | `C:\Tools\Rufus\` | USB інструмент, не для dev |
| NSwag | 14.7 | `C:\Users\agga\.dotnet\tools\nswag.exe` | OpenAPI → C# DTO gen |
| uv | latest | `C:\Users\agga\.local\bin\uv.exe` | Python package manager |

---

## Python backend

- **Python:** 3.13 (venv у `.venv/`)
- **Package manager:** `uv` → `C:\Users\agga\.local\bin\uv.exe`
- **Task runner:** `just` → `C:\Tools\just\just.exe`
- **Framework:** FastAPI 0.100+ + SQLAlchemy 2.0+ + Pydantic 2.0+ + APScheduler 3.11
- **DB:** PostgreSQL 16 (Docker container `city-economic-simulator-postgres`)
- **Migrations:** Alembic
- **Tests:** pytest (124 тести, всі проходять)
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

### OpenAPI → C# DTO Generation

- **Tool:** NSwag.ConsoleCore 14.7 (`C:\Users\agga\.dotnet\tools\nswag.exe`)
- **Generator:** `nswag openapi2csclient`
- **Output:** `client/scripts/generated/CityApiModels.cs`
- **Format:** System.Text.Json (Godot .NET compatible)

```bash
# Backend має бути запущений на :8000
just generate-api-client
```

Це створює type-safe C# DTO класи з усіх FastAPI Pydantic models.

## MCP Servers (AI розширення)

### 1. Godot MCP Bridge (локальний, завжди доступний)

- **Скрипт:** `scripts/godot_mcp_bridge.py`
- **WebSocket:** `ws://127.0.0.1:6505` (Godot ↔ Bridge)
- **HTTP Control:** `http://127.0.0.1:6507`
- **Status:** `GET http://127.0.0.1:6507/status`
- **Invoke:** `POST http://127.0.0.1:6507/invoke`

```bash
just mcp-bridge          # запустити bridge
just mcp-status          # перевірити статус
.\ scripts\invoke_godot_mcp.ps1  # виклик інструменту
```

Доступні tools: `get_errors`, `get_console_log`, `scene_tree_dump`, `get_project_settings`, `file_tools`, `script_tools`

**Коли використовувати:** після будь-яких змін у C# скриптах або `.tscn` сценах — викликати `get_errors` перед комітом.

---

### 2. Playwright MCP (Microsoft, локальний через npx)

- **Пакет встановлено:** `C:\Tools\nodejs\node_modules\@playwright\mcp\cli.js`
- **Версія:** 0.0.75
- **Config:** `C:\Users\agga\.codeium\windsurf\mcp_config.json` ✅ налаштовано

**Що робить:** керує реальним браузером — navigate, click, screenshot, E2E тести.

**Коли використовувати:**
- Smoke test `localhost:8000/docs` після запуску backend
- Перевірка що API endpoint відповідає
- Screenshot dashboard для visual QA

---

### 3. Context7 MCP (Upstash, локальний через npx, без API key)

- **Пакет встановлено:** `C:\Tools\nodejs\node_modules\@upstash\context7-mcp\dist\index.js`
- **Config:** `C:\Users\agga\.codeium\windsurf\mcp_config.json` ✅ налаштовано

**Що робить:** підтягує актуальну документацію бібліотек прямо в контекст.

**Коли використовувати:**
- При роботі з FastAPI, SQLAlchemy, APScheduler, Pydantic, Alembic
- Додавай `use context7` до запиту щоб отримати актуальні доки

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

## Scripts у `scripts/` — що є і коли використовувати

| Скрипт | Коли використовувати |
|--------|---------------------|
| `check.ps1` | Перед кожним комітом — pytest + C# build |
| `play.ps1 -ResetDb` | Playtest з нуля — скидає БД і запускає все |
| `smoke_godot_dashboard.ps1` | Після змін у dashboard C# — smoke через MCP |
| `capture_dashboard.ps1` | Visual QA — скриншот поточного стану UI |
| `smoke_mvp.py` | Після змін backend API — HTTP smoke test |
| `start_backend.ps1` | Запустити тільки backend без Godot |
| `reset_dev_db.ps1` | Скинути БД до чистого стану |
| `godot_mcp_bridge.py` | MCP bridge для Godot — запустити перед роботою зі сценами |
| `invoke_godot_mcp.ps1` | Виклик конкретного MCP tool у Godot |
| `build_anime_avatar.ps1` | Генерація anime GLB аватара через Blender |
| `capture_anime_avatar.ps1` | Screenshot аватара для QA |

## Що можна додати в майбутньому

- `structlog` — структуроване логування замість basicConfig
- Sentry MCP — error monitoring після першого деплою
- GitHub MCP — читати CI статус і issues прямо з чату

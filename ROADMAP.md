# Roadmap: City Economic Simulator MVP

Цей roadmap фіксує напрямок розробки так, щоб гра спершу стала стабільним MVP, а вже потім обростала великими системами.

## Phase 0 - Dev Foundation

Goal: проєкт має запускатися, тестуватися і бути зрозумілим з першого відкриття.

- Зафіксувати локальний стек: Python 3.12+, Godot 4.3 .NET, .NET SDK 8.
- Додати `.env.example` і читати `CITY_DATABASE_URL`, `CITY_CORS_ORIGINS`, `CITY_DEBUG`.
- Використовувати PostgreSQL одразу; SQLite не підтримується навіть локально.
- Винести стартовий seed міста з `main.py` в окремий модуль.
- Додати мінімальні pytest-тести на першу ігрову петлю.
- Додати `.gitignore`, щоб база, кеші та build-артефакти не заважали.

## Phase 1 - 5-Minute Core Loop

Goal: гравець за 5 хвилин проходить зрозумілий шлях "старт -> робота -> сон -> освіта -> краща робота".

- REST API для команд: register, get player, vacancies, apply job, work shift, sleep, exam info, submit exam.
- WebSocket тільки для live-подій: чат, міські новини, події економіки, broadcast змін.
- Єдиний формат відповіді API: `success`, `message`, `data`, `effects`.
- Усі грошові операції проводити через ledger/service, який робить debit/credit/log в одній DB-транзакції.
- Показувати прогрес до найближчої цілі: освіта, баланс, стабільність, репутація.

## Phase 2 - Architecture Split

Goal: backend перестає бути одним великим файлом.

- `backend/app/main.py` - створення FastAPI app.
- `backend/app/api/routes/*.py` - маршрути.
- `backend/app/schemas/*.py` - Pydantic DTO.
- `backend/app/services/*.py` - бізнес-сценарії.
- `backend/app/repositories/*.py` - повторювані DB-запити.
- `backend/app/core/*.py` - config, logging, security.
- `backend/app/realtime/*.py` - WebSocket manager.

## Phase 3 - Economy Balance

Goal: економіка відчувається як система, а не як набір кнопок.

- Зробити `game_day_tick`: оренда, кредити, інфляція, випадкові події, decay настрою/енергії.
- Зберігати `money_supply_snapshot` для інфляції за формулою з `database/economic_formulas.md`.
- Ввести money sinks: освіта, житло, їжа/сон, штрафи, ліцензії.
- Обмежити "друк грошей" державними зарплатами через бюджет міста.
- Використовувати `BusinessBlueprint` як джерело правди для player-built бізнесів: allowed land/zoning, city metric effects, opening fee, risk, upkeep і теоретична прибутковість.
- Додати daily upkeep для активних player-built будівель як перший money sink перед повною симуляцією cashflow.
- Додати баланс-тести: за N днів гравець не має ламати економіку нескінченними циклами.

## Phase 4 - Godot MVP Client

Goal: клієнт показує реальну петлю гри, а не тільки WebSocket demo.

- Створити головну сцену `city_dashboard.tscn`.
- Додати autoload `NetworkManager`.
- Додати REST-клієнт для команд і WebSocket-клієнт для live-подій.
- Екрани MVP: dashboard, jobs, hostel/sleep, education exam.
- Локальний dev-профіль: `http://127.0.0.1:8000` і `ws://127.0.0.1:8000`.

## Phase 5 - Multiplayer Readiness

Goal: підготувати перехід від локального MVP до онлайн-міста.

- PostgreSQL через Alembic migrations.
- Redis для presence/session/cache.
- Auth/session tokens.
- Idempotency keys для економічних команд.
- Row-level locking або optimistic concurrency для грошей і вакансій.
- Rate limits на роботу, сон, іспити та тіньові дії.

## What Not To Add Yet

Поки core loop не грається добре, ці системи краще тримати як майбутні двері:

- Повна політика міста.
- Картелі, страхування і профспілки як основний gameplay.
- Велика спортивна ліга.
- Повний бізнес-менеджмент.
- Мобільний реліз.

## Suggested Tooling

Required:

- Python 3.12+.
- Godot 4.3 .NET edition.
- .NET SDK compatible with the Godot version.
- PostgreSQL 16+ або Docker Desktop для Postgres контейнера.
- Git.

Recommended:

- VS Code або Rider.
- pgAdmin або DBeaver.
- HTTP-клієнт: Bruno, Insomnia або Postman.

Optional later:

- Redis 7+.

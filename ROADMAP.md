# Roadmap: City Economic Simulator MVP

Цей roadmap фіксує напрямок розробки так, щоб гра спершу стала стабільним MVP, а вже потім обростала великими системами.

## Phase 0 - Dev Foundation ✅ COMPLETE

Goal: проєкт має запускатися, тестуватися і бути зрозумілим з першого відкриття.

- [x] Зафіксувати локальний стек: Python 3.12+, Godot 4.3 .NET, .NET SDK 8.
- [x] Додати `.env.example` і читати `CITY_DATABASE_URL`, `CITY_CORS_ORIGINS`, `CITY_DEBUG`.
- [x] Використовувати PostgreSQL одразу; SQLite не підтримується навіть локально.
- [x] Винести стартовий seed міста з `main.py` в окремий модуль (`backend/app/seed.py`).
- [x] Додати мінімальні pytest-тести на першу ігрову петлю (90 тестів проходять).
- [x] Додати `.gitignore`, щоб база, кеші та build-артефакти не заважали.
- [x] **Додатково:** Сучасний dev stack: `just`, `ruff`, `pyright`, `uv`, `pre-commit`, `TOOLS.md` документация.

## Phase 1 - 5-Minute Core Loop ✅ COMPLETE

Goal: гравець за 5 хвилин проходить зрозумілий шлях "старт -> робота -> сон -> освіта -> краща робота".

- [x] REST API для команд: register, get player, vacancies, apply job, work shift, sleep, exam info, submit exam.
- [x] REST API для першої забудови: city land parcels, business blueprints, building applications, activation, portfolio, open/repair actions.
- [x] WebSocket тільки для live-подій: чат, міські новини, події економіки, broadcast змін.
- [x] Єдиний формат відповіді API: `success`, `message`, `data`, `effects`.
- [x] Усі грошові операції проводити через ledger/service, який робить debit/credit/log в одній DB-транзакції.
- [x] Показувати прогрес до найближчої цілі: освіта, баланс, стабільність, репутація.
- [x] **Додатково:** Sports API (клуби, тренування, контракти), Onboarding API, Avatar creation API.

## Phase 2 - Architecture Split 🔄 80% COMPLETE

Goal: backend перестає бути одним великим файлом.

- [x] `backend/app/main.py` - створення FastAPI app.
- [x] `backend/app/api/routes/*.py` - маршрути (mvp.py, frozen.py).
- [x] `backend/app/schemas/*.py` - Pydantic DTO (mvp.py, response.py).
- [x] `backend/app/services/*.py` - бізнес-сценарії (24 services).
- [🔄] `backend/app/repositories/*.py` - повторювані DB-запити (7 репозиторіїв, 8/14 services мігровано).
- [x] `backend/app/core/*.py` - config, logging, security (config.py, exceptions.py).
- [x] `backend/app/realtime/*.py` - WebSocket manager (manager.py).

## Phase 3 - Economy Balance 🔄 60% COMPLETE

Goal: економіка відчувається як система, а не як набір кнопок.

- [x] Зробити `game_day_tick`: оренда, кредити, інфляція, випадкові події, decay настрою/енергії.
- [x] Зберігати `money_supply_snapshot` для інфляції за формулою з `database/economic_formulas.md`.
- [x] Ввести money sinks: освіта, житло, їжа/сон, штрафи, ліцензії.
- [x] Обмежити "друк грошей" державними зарплатами через бюджет міста.
- [x] Використовувати `BusinessBlueprint` як джерело правди для player-built бізнесів: allowed land/zoning, city metric effects, opening fee, risk, upkeep і теоретична прибутковість.
- [x] Додати daily upkeep для активних player-built будівель як перший money sink перед повною симуляцією cashflow.
- [x] Додати repair/reopen flow для `maintenance_due`, щоб прострочене утримання було м'яким ігровим станом, а не безвихідною втратою активу.
- [x] Додати building portfolio API як контракт для Godot UI: статуси, fees, blueprint summary і доступні дії.
- [🔄] Додати баланс-тести: за N днів гравець не має ламати економіку нескінченними циклами (потрібна реалізація).

## Phase 4 - Godot MVP Client 🔄 70% COMPLETE

Goal: клієнт показує реальну петлю гри, а не тільки WebSocket demo.

- [x] Створити головну сцену `city_dashboard.tscn`.
- [x] Додати autoload `NetworkManager`.
- [x] Додати REST-клієнт для команд і WebSocket-клієнт для live-подій.
- [x] Екрани MVP: dashboard, jobs, hostel/sleep, education exam.
- [x] Dashboard показує перший фізичний asset гравця: building portfolio, статуси, fees і доступні open/repair дії з backend.
- [x] Локальний dev-профіль: `http://127.0.0.1:8000` і `ws://127.0.0.1:8000`.
- [🔄] **Проблема:** `CityDashboardController.cs` — 95KB моноліт, потребує рефакторингу на partial classes.
- [x] **Додатково:** OpenAPI → C# DTO generation, Godot MCP addon, Avatar system.

## Phase 5 - Multiplayer Readiness 🔄 85% COMPLETE

Goal: підготувати перехід від локального MVP до онлайн-міста.

- [x] PostgreSQL через Alembic migrations.
- [ ] Redis для presence/session/cache.
- [x] Auth/session tokens.
- [x] Idempotency keys для економічних команд.
- [x] Row-level locking або optimistic concurrency для грошей і вакансій.
- [x] Rate limits на роботу, сон, іспити та тіньові дії.

## Phase 6 - Production Ready 🔄 20% COMPLETE

Goal: стабільний продакшн-готовий проєкт з документацією та моніторингом.

- [ ] Docker Compose для продакшн deployment.
- [ ] CI/CD pipeline (GitHub Actions).
- [ ] Моніторинг та логування (Prometheus/Grafana).
- [ ] Health checks та graceful shutdown.
- [ ] Performance optimization та profiling.
- [ ] Security audit та hardening.

---

## 🎯 Поточні Пріоритети (Sprint 52)

### 1. Завершити Repository Layer (2-3 дні)
- [ ] Мігрувати 6 services: `sports.py`, `player_profile.py`, `onboarding.py`, `advanced.py`, `buildings.py`, `business_blueprints.py`
- [ ] Перевірити всі тести після міграції
- [ ] Додати відсутні репозиторії за потреби

### 2. Рефакторинг CityDashboardController.cs (3-4 дні)
- [ ] Розбити 95KB моноліт на partial classes
- [ ] Створити окремі controllers для UI секцій
- [ ] Інтегрувати згенеровані C# DTOs
- [ ] Виправити memory leaks та performance issues

### 3. Balance Testing & Economy Validation (2-3 дні)
- [ ] Написати баланс-тести для day tick
- [ ] Симуляція 30-днів ігрового циклу
- [ ] Перевірити економічні формули
- [ ] Виправити знайдені дисбаланси

### 4. Production Infrastructure (2-3 дні)
- [ ] Налаштувати Redis для session management
- [ ] Docker Compose для продакшн
- [ ] Health checks та monitoring endpoints
- [ ] CI/CD pipeline для автоматичних деплойментів

---

## 🚀 Можливі Покращення та Розвиток

### Short-term (1-2 місяці)
1. **Mobile-First UI** — адаптивний дизайн для мобільних пристроїв
2. **Real-time Notifications** — push сповіщення для подій міста
3. **Player Profiles** — соціальні профілі та статистика
4. **Marketplace** — гравець-до-гравця торгівля
5. **Achievements System** — гейміфікація прогресу

### Medium-term (3-6 місяців)
1. **Multiplayer Cities** — кілька міст на одному сервері
2. **Political System** — вибори мера, голосування, закони
3. **Advanced AI** — NPC з поведінкою та рішеннями
4. **Weather System** — динамічна погода що впливає на економіку
5. **Mod Support** — можливість додавати контент

### Long-term (6+ місяців)
1. **Web Client** — браузерна версія гри
2. **Mobile Apps** — нативні iOS/Android додатки
3. **Blockchain Integration** — NFT активи та DeFi елементи
4. **VR/AR Support** — імерсивний досвід
5. **AI-powered NPCs** — LLM-інтегровані персонажі

---

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

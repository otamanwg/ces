# Roadmap: City Economic Simulator MVP

Єдиний актуальний roadmap проєкту. Якщо є сумнів між файлами, джерелом правди є саме `ROADMAP.md`.
`SOLO_ROADMAP.md` лишається тільки як архівний вказівник.

## Agent Operating Model

- Працюй top-down: спочатку `TOOLS.md`, потім цей файл, потім релевантний код, потім тести.
- Один slice = одна причина. Не бандли дрібні фікси разом.
- Backend before client: спочатку контракт + тести, потім Godot/C#.
- Для кожного slice: regression test -> minimal fix -> найменший релевантний `scripts/check_targeted.ps1 <profile>` або `just check-...` -> `scripts/check.ps1` тільки перед закриттям slice / після інтеграції кількох targeted-змін / перед milestone handoff -> update roadmap.
- Якщо задача змінює сцену або C# у клієнті, перевір Godot MCP `get_errors` перед завершенням.
- Зупинка тільки якщо потрібне продуктове рішення, schema change, або 2 поспіль невдалі спроби.
- Не відкривати нові системи, поки поточна черга не закрита і core loop не стабільний.

## Parallel Execution Rules

- Головний агент володіє інтеграцією, архітектурними рішеннями, roadmap і фінальним quality gate.
- Субагенти отримують лише незалежні задачі з чітким read/write scope.
- Один файл або модуль одночасно має лише одного writer; паралельні аудити залишаються read-only.
- PostgreSQL test suites завжди запускаються послідовно: fixtures скидають і мігрують спільну test schema.
- Результат субагента не вважається готовим, доки головний агент не переглянув diff і не запустив релевантні тести.
- `scripts/check.ps1` та оновлення цього roadmap виконуються після інтеграції кожного завершеного slice.
- Targeted profiles є стандартним циклом розробки, не допоміжною опцією. Для routine iteration не ганяти весь проєкт, якщо зміна має чіткий локальний профіль.
- Targeted profiles не замінюють full gate; вони зменшують цикл під час розробки slice, а full gate лишається фінальною перевіркою.
- Розвивай проєкт пропорційно: production/infrastructure fixes не мають випереджати playable gameplay/client foundation. Після кожного інфраструктурного блоку повертай фокус до core loop, Godot UX або видимого міста.

## Stabilization Gate — Before New Features

Поки gate не закритий, дозволені лише виправлення, завершення вже початих refactor slices та інструменти контролю якості.

1. [x] Виправити repository regression: повернути `124 passed / 0 failed`.
2. [x] Закрити всі поточні `pyright` errors і додати lint/typecheck та client logic tests до локального/CI gate.
3. [x] Завершити partial-class merge без backup/wip-артефактів; client tests і build зелені.
4. [x] Узгодити Docker Compose/Dockerfile з реальними `CITY_*` settings, PostgreSQL driver і module path.
5. [x] Додати спільний `AGENTS.md`, `scripts/doctor.ps1`, secret scan і ігнорування локальних MCP-артефактів.
6. [x] Фінальний gate: `check.ps1`, API smoke, Godot MCP smoke і review робочого дерева.

## Current Execution Queue — Sprint 60

1. [x] Інтегрувати перші partial slices (`Onboarding`, `PlayerActions`, `Visual`) у бойовий controller без ламання client build.
2. [x] Прибрати backup/wip-артефакти після partial-class merge.
3. [x] Домігрувати repository layer у сервісах: `sports.py`, `player_profile.py`, `onboarding.py`, `advanced.py`, `buildings.py`, `business_blueprints.py`.
4. [x] Додати детерміновану 30-денну economy validation із явними acceptance-порогами.
5. [x] Закрити мінімальний production checklist: CI, Docker, health, Redis, monitoring gaps, graceful shutdown.
6. [x] Винести character creation/avatar selection у окремий partial без зміни поведінки.
7. [x] Винести building flow (`land -> application -> activation`) в окремий partial, не змішуючи з portfolio/open/repair.
8. [x] Винести building portfolio lifecycle (`load -> open/repair`) в окремий partial після окремого аудиту меж.
9. [x] Винести guided player-action responses і pending cleanup у `PlayerActions` з pure endpoint classifier tests.
10. [x] Винести решту specialized response routing (`BuildingFlow`, `BuildingPortfolio`, business status) з central dispatcher.
11. [x] Захистити API callback від malformed/empty JSON через testable response parser.
12. [x] Винести generic API envelope, transport errors і pending orchestration в `ApiDispatch` partial.
13. [x] Прибрати локальний `PytestCacheWarning` (`WinError 5`) без послаблення test gate.
14. [x] Додати client API dispatch smoke coverage для malformed payload і pending-state recovery на рівні Godot runtime.
15. [x] Винести player/city presentation update methods у окремий partial після аудиту cohesive boundaries.
16. [x] Додати scheduler leader lock, щоб кілька backend replicas не запускали один economy tick паралельно.
17. [x] Додати HTTP request IDs і JSON-ready structured logging для production diagnostics.
18. [x] Винести Alembic міграції в окремий production migration job замість запуску всередині app startup.
19. [x] Замінити plaintext player auth tokens на hashed token storage з backward-safe migration path.
20. [x] Передавати player token у WebSocket client connection і покрити це client/backend tests.
21. [x] Додати production Prometheus/Grafana stack із provisioned datasource/dashboard і smoke-перевіркою scrape.
22. [x] Додати `city_economy_snapshots` і day-over-day inflation formula для 30-денного economy gate.
23. [x] Додати ізольований production backup/restore drill для PostgreSQL logical dumps.
24. [x] Додати rollout preflight і rollback strategy для production deploy.
25. [x] Посилити production secrets/monitoring guardrails: env ignore, localhost-only monitoring, stricter config validation, wider secret scan.
26. [x] Перевести production credentials на Docker secrets / `_FILE` contract для PostgreSQL, backend/migrate, Redis і Grafana.
27. [x] Додати release metadata contract (`CITY_RELEASE_*`) і schema version у health/readiness для rollout verification.
28. [x] Посилити backup/restore drill sentinel data та row-count validation для ключових таблиць.
29. [x] Додати optional restore validation mode для зовнішнього production dump без створення нового dump.
30. [x] Додати manual/scheduled/deploy-path CI workflow для isolated production smoke stack.
31. [x] Додати immutable backend image publishing/tagging contract із OCI labels і `release.env` artifact.
32. [x] Додати staging/non-local host runbook для registry login, release env, pull і no-build deploy.
33. [x] Провести Godot playability audit через реальний запуск клієнта: diagnostics, landscape viewport, core loop, onboarding, visual feel.
34. [x] Додати перший city/street focus layout: місто і персонаж стають головним ігровим станом, side report прибирається.
35. [x] Додати gameplay HUD polish для city/street focus: район, робота, ризик і стан будівель читаються поверх міста.
36. [x] Додати перший pass gameplay HUD під city/street focus: next action, ціль і наслідки видно в першому viewport.
37. [ ] Переробити решту dashboard у більш ігровий екран: події, цілі й основні дії мають читатись як gameplay HUD, не як звіт.
38. [ ] Довести arrival onboarding flow: вокзал -> крадіжка -> поліція або житло -> передача керування.
39. [ ] Додати перший visible city layer MVP: райони, physical building markers, zoom/focus states, без повної SimCity-системи.
40. [ ] Посилити business/building guidance у UI: вартість, земля, ризик, theoretical profit, upkeep, visual archetype.

## Open Debt Register

- `CityDashboardController.cs` зменшено до 535 рядків; presentation та API orchestration ізольовані у власних partial-ах.
- API response parser розрізняє valid/empty/malformed payload і не залишає UI action у pending-стані.
- Pytest cache працює через ignored `.cache/pytest`; повний gate проходить без warnings.
- `check.ps1` запускає headless Godot runtime smoke для API dispatch recovery.
- Repository migration Sprint 59 завершена; ширший debt поза sprint є в economy/business services і ведеться окремими slices.
- Economy snapshots зберігають `M_t`, `M_{t-1}`, growth та inflation; 30-денний gate перевіряє day-over-day формулу.
- Scheduler має Redis leader lease та PostgreSQL advisory execution fence; Redis outage зупиняє scheduled ticks до відновлення leadership.
- HTTP responses мають `X-Request-ID`; production logs підтримують JSON формат із `request_id`.
- Production backend чекає one-shot `migrate` service; app startup більше не запускає Alembic у production.
- Player auth tokens зберігаються hash-first; legacy plaintext записи backfill/cleanup через migration і fallback lookup.
- Production backup/restore drill із sentinel data/row-count validation, external dump validation mode, rollout preflight, rollback strategy, baseline secrets guardrails, Docker secrets / `_FILE` contract і release metadata є.
- Production expansion заморожений до нового рішення; reverse proxy/TLS staging dry-run чекатиме вибору домену або хоста.
- Наступний активний debt: Godot playability audit і client/gameplay-first slice.
- Test workflow оптимізований через `scripts/check_targeted.ps1` і `just check-*`; це default dev loop. Full gate лишається фінальною перевіркою, а не основним способом ітерації.

## Progress Snapshot

- Phase 0 — Dev Foundation: 100%
- Phase 1 — 5-Minute Core Loop: 100%
- Phase 2 — Architecture Split: 100%
- Phase 3 — Economy Balance: 82%
- Phase 4 — Godot MVP Client: 75%
- Phase 5 — Multiplayer Readiness: 90%
- Phase 6 — Production Ready: 99%

## Verified Now

- Backend tests: `155 passed / 0 failed`.
- Client logic tests: passed; Godot C# build: passed, 0 warnings/errors.
- Controller split: main controller — 535 рядків; API dispatch, presentation, guided actions і feature routing рознесені по partial-ах.
- Ruff lint/format: passed; pyright: `0 errors`.
- API smoke: повний MVP loop passed; Godot MCP dashboard smoke: `0 errors`.
- Economy gate: 30 production days, solvency/needs/ledger/business/upkeep/inflation acceptance passed.
- Economy snapshots: `city_economy_snapshots` created through Alembic; 30-day gate verifies daily `M_t -> M_{t-1}` chain and day-over-day inflation formula.
- CI: migrations, Ruff, pyright, secret scan, backend pytest, client logic tests, Godot C# build і production Compose validation.
- Production config fail-closed: явні PostgreSQL/Redis/CORS settings, debug/docs/frozen routes вимкнені.
- Graceful shutdown: scheduler, Redis, SQLAlchemy engine і WebSocket DB sessions коректно звільняються.
- Scheduler scale-out safety: одна replica тримає Redis lease; PostgreSQL advisory lock не допускає паралельний tick одного міста.
- Request diagnostics: `X-Request-ID` проходить через HTTP response і backend log context; production env вмикає `CITY_LOG_FORMAT=json`.
- Production migrations: `docker-compose.prod.yml` має one-shot `migrate`; backend залежить від `service_completed_successfully`.
- Auth token storage: нові player tokens повертаються клієнту один раз, у БД зберігається `auth_token_hash`; legacy plaintext очищується після backfill/fallback.
- WebSocket client auth: city WS URL будується через encoded `?token=...`, guest state не відкриває WS.
- Monitoring stack: production Compose має Prometheus/Grafana, provisioned datasource/dashboard і smoke-перевірку scrape.
- Backup/restore drill: `scripts/drill_backup_restore.ps1` seeds sentinel rows, creates a PostgreSQL dump, restores it into a validation database, verifies migration/schema markers, compares key table row counts, and checks sentinel money-supply data in an isolated Compose project.
- External backup validation: `scripts/drill_backup_restore.ps1 -ValidateExistingBackup -BackupPath ... -ExpectedRowCounts ...` restores an existing dump into an isolated validation database without creating a new dump.
- Production smoke CI: `.github/workflows/production-smoke.yml` runs the isolated production stack manually, weekly, and on deploy-related PR/push path changes.
- Release image contract: `.github/workflows/release-image.yml` builds/publishes `ghcr.io/<owner>/<repo>/ces-backend:<git-sha>`, uploads `release.env`, and Docker/Compose tags carry matching release metadata.
- Remote deploy runbook: `DEPLOYMENT.md` documents registry login, `release.env` application, `docker compose pull`, `up --no-build`, and runtime release identity checks for staging/non-local hosts.
- Proportional development rule: production foundation is sufficient for now; next work must improve playable Godot UX, onboarding, visible city, or core gameplay clarity.
- Godot playability audit: real dashboard scene launched through MCP with `is_playing=true`, `get_errors=0`; visual QA captures now show onboarding/story/street states instead of being blocked by character creation.
- City focus slice: street focus hides the report rail, expands the city visual, keeps actions available, shows a compact gameplay HUD, and capture preview can force an avatar for visual QA.
- Gameplay HUD pass: street focus now keeps next action, goal progress and immediate effects visible under the city view; building/report panels stay out of the first viewport while focused.
- Rollout strategy: `scripts/rollout_preflight.ps1` validates env hardening, prod-fast, Compose config, backup drill, and isolated production smoke before deployment; `DEPLOYMENT.md` documents rollback paths.
- Secrets/monitoring guardrails: `.env.production` ignored, production config rejects unsafe URLs/CORS, secret scan covers staged/untracked env-style leaks, Prometheus/Grafana bind to localhost.
- Docker secrets: production Compose uses secret files for Postgres, app DB/Redis URLs, Redis password, and Grafana admin password; production smoke and backup/restore drill pass with file-backed secrets.
- Release metadata: production requires `CITY_RELEASE_SHA`, `CITY_RELEASE_IMAGE`, and `CITY_RELEASE_VERSION`; `/health` and `/health/ready` expose release metadata plus Alembic schema version.
- Observability baseline: liveness/readiness endpoints і Prometheus-compatible `/metrics`.
- Production Docker smoke: backend, PostgreSQL і Redis healthy; readiness/metrics passed; DB/Redis не мають host ports.
- Godot MCP, Playwright MCP, Context7 MCP, `just`, `ruff`, `pyright`, `uv`, `pre-commit` уже доступні як dev tools.

## Frozen Until MVP Is Stable

- sports, shadow economy, cartels, unions, insurance, advanced routes.
- Нові системи не брати, поки current queue не закрита і 5-minute loop не відчувається стабільним.

## Reference Inputs

- Gameplay north star: `GAMEPLAY_CORE_MODEL.md`
- Tool inventory: `TOOLS.md`
- User-facing overview: `README.md`

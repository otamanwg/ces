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
37. [x] Переробити решту dashboard у більш ігровий екран: події, цілі й основні дії мають читатись як gameplay HUD, не як звіт.
38. [x] Довести arrival onboarding flow: вокзал -> крадіжка -> поліція або житло -> передача керування.
39. [x] Додати перший visible city layer MVP: райони, physical building markers, zoom/focus states, без повної SimCity-системи.
40. [x] Посилити business/building guidance у UI: вартість, земля, ризик, theoretical profit, upkeep, visual archetype.

## Post-MVP Gameplay Phases — SimCity 4-Inspired Citizen Model

Джерело дизайну: `GAMEPLAY_CORE_MODEL.md` (розділи 13-29). Кожна фаза — це backend-first slice з тестами, без UI/3D, поки не вказано інше.

### Phase G1 — Dynamic District Metrics (ACTIVE)

Каркас динамічних метрик районів + композитні індекси + сезонність. Backend-only.

1. [x] Міграція `add_district_metrics_and_foundation`:
   - Нові поля `CityDistrict`: `pollution`, `education_coverage`, `fire_safety`, `power_supply`, `water_supply`, `waste_management`, `population`, `housing_capacity`, `green_space`, `happiness` (Float, default 50.0).
   - Нова таблиця `district_metric_snapshots` (історія по днях).
   - Фундаментні таблиці (порожні, без сервісів): `skins`, `player_skins`, `education`, `education_exams`, `criminal_rep_log`, `corruption_log`, `press_investigations`, `court_cases`, `prison_sentences`, `casino_games`, `shadow_businesses`, `lawyer_engagements`, `press_blackmails`.
   - Нові поля `Player`: `criminal_rep` (Float, default 0), `successful_deals` (Int, default 0).
2. [x] Сервіс `district_metrics.py`: формули всіх метрик + feedback loops + композитні індекси (economy/production/household/commerce/infrastructure/social, 0-100).
3. [x] Сервіс `season_service.py`: сезонні множники (константи), весна як стартовий сезон, плавний перехід 7 днів.
4. [x] Day tick інтеграція: оновлення метрик + snapshot.
5. [x] API `/api/districts/{id}/radar`: 6 композитних індексів + тренд за 7 днів.
6. [x] Тести: day tick оновлює метрики, feedback loops, сезони, snapshot, radar endpoint (20 passed).

### Phase G2 — NPC Residents (DONE)

Полегшені NPC-акаунти як робітники і споживачі.

1. [x] Таблиця `npc_residents` (окрема від `Player`): `district_id`, `workplace_business_id`, `cash_balance`, `salary`, `employed_at`, `npc_type`.
2. [x] Сервіс `npc_service.py`: генерація (явний найм через API), звільнення (стирається як видалений акаунт), ліміти за legal_form (ФОП=1, ТОВ=5, ВАТ=10).
3. [x] Цикл витрат: рандомні дії з ймовірністю 70%, баланс кешу в коридорі [20, 500] (не банкрут, не накопичує).
4. [x] ЗП і премія двічі на місяць (8-10 день ЗП, 20-23 премія 20%).
5. [x] Day tick інтеграція: payroll + spending для вже найнятих NPC (генерація — явна).
6. [x] API: `/businesses/{id}/npcs` (список), `/businesses/{id}/npcs/hire`, `/businesses/{id}/npcs/{npc_id}/dismiss`.
7. [x] Інтеграція з district_metrics: NPC входять у population району.
8. [x] Тести: 28 passed (ліміти, генерація, звільнення, ЗП, премія, витрати, API, day tick, metrics).

### Phase G3 — Utility Services as Businesses (DONE)

Комунальні служби (електростанція, водоканал, сміттєзавод) як бізнеси.

1. [x] Blueprint-категорія `utility` (power_plant, water_works, waste_plant).
2. [x] Комунальні платежі йдуть службам → служби платять у казну (10% податок), мають свій баланс.
3. [x] Банкрутство служби → екстрений контракт з сусіднім містом за завищеними цінами (3x), різницю платить мерія.
4. [x] Попередження у мера про проблеми з усіма службами (high load, low balance, no service, emergency).
5. [x] Інтеграція з district_metrics: реальні потужності utility замість базових 100.
6. [x] API `/city/utility-status`: статус служб + попередження мера.
7. [x] Тести: 18 passed (blueprints, payments, bankruptcy, emergency contracts, warnings, metrics, API, day tick).

### Phase G4 — Vacancies and Hiring (NPC + Players) (DONE)

1. [x] Розширення вакансій: ЗП фіксована по типу бізнесу (почасова статична), премія % від чистого прибутку (власник виставляє, до 50%).
2. [x] Найм NPC (до ліміту: ФОП 1, ТОВ 5, ВАТ 10) — Phase G2; гравець-вакансії — Phase G4.
3. [x] Гравець-власник може працювати сам (витрачає енергію, без ЗП — дивіденди).
4. [x] Звільнення гравця-працівника за бажанням власника.
5. [x] Біржа "для студентів" (очна освіта — лише вечірні зміни, shift_type="student").
6. [x] API: /vacancies/player, /vacancies/student, /businesses/{id}/vacancies, /businesses/{id}/owner-work, /jobs/{id}/fire.
7. [x] Тести: 19 passed (fixed salary, post vacancy, apply, fire, owner-works, student vacancies, API).

### Phase G5 — Bank as Business (DONE)

1. [x] Blueprint `bank` (category="finance", оперує з власного cash_balance).
2. [x] Кредити (банк видає з власного балансу, гравець обирає ставку через API).
3. [x] Депозити від гравців + щоденне нарахування відсотків.
4. [x] Банкрутство бізнесу → аукціон (24 години реального часу, стартова ціна = борги + 10% місту, будь-який гравець).
5. [x] API: /banks/{id}/deposit, /banks/deposits/{id}/withdraw, /banks/{id}/loan, /banks/loans/{id}/repay, /auctions/active, /auctions/{id}/bid.
6. [x] Тести: 23 passed (deposits, loans, interest, auctions, bidding, closing, API).

### Phase G6 — Political System (DONE)

1. [x] Ієрархія посад у мерії (worker → department_head → deputy → mayor). Робота в мерії 90 днів — вимога для балотування.
2. [x] Вибори мера: вимоги (репутація ≥50, освіта ≥College, 90 днів у мерії), відкрите голосування, мандат 180 днів, вотум недовіри.
3. [x] Підкуп голосів: тіньовий фонд, анонімна пропозиція, виборець може прийняти/відхилити/повідомити (30% шанс), political_corruption_log з evidence_strength.
4. [x] AI-мер: інвестує з treasury у район з найгіршим desirability.
5. [x] API: /city/offices/hire, /city/election (GET/start/register/vote/conclude), /city/election/bribe, /city/no-confidence, /city/ai-mayor-invest.
6. [x] Тести: 25 passed (office hierarchy, candidacy, elections, voting, no-confidence, bribery, AI mayor, API).

### Phase G7 — 3D Avatar and Locations (Godot) (DONE)

1. [x] `PlayerAvatar.tscn`: 3D-персонаж (CharacterBody3D + canonical_anime_avatar.glb), базові анімації (idle/walk/run через AnimationPlayer), third-person камера, WASD + миша.
2. [x] Скін-система: існуюча AvatarAppearanceResolver (зачіска, обличчя, очі, губи, зріст, вага, костюм, кольори) — вже працює з G7 аватаром.
3. [x] Перша локація: `CityStreetLocation.tscn` (підлога, освітлення, fog, портал до дашборду через LocationPortal.cs).
4. [x] WebSocket-синхронізація позиції гравця: NetworkManager.SyncPlayerPosition (6.7Hz), backend broadcast `type: "position"`.
5. [x] Godot MCP diagnostics: editor connected, is_playing=true, get_errors=0, scene_tree_dump підтверджує повне дерево (avatar skeleton + portal + camera).

### Phase G8 — Prison, Police, Press, Court, Lawyer (DONE)

1. [x] PrisonLocation.tscn — відкладено до G9 (3D-локації). Backend готовий: prison_service.py.
2. [x] Гравець-поліцейський: ієрархія Patrol → Detective → Chief, патрулювання (випадкові події), арешт, конфіскація. Начальник призначається мером (90 днів стажу).
3. [x] Преса як бізнес: розслідування (press_evidence), публікація (happiness/reputation impact), реклама, шантаж (НЕ впливає на репутацію журналіста).
4. [x] Суд: автоматичний вердикт за evidence_strength (fine/license_revoked/candidacy_revoked/mandate_revoked/criminal_case), апеляція (3 AI-судді з corruption_resistance 0.3-0.9), підкуп суддів, невдалий хабар = подвоєне покарання.
5. [x] Адвокат: супровід угод (10% комісія, success_chance_bonus за рівнем), апеляція, захист від поліції. Рівень росте за успішними угодами.
6. [x] Конфіскація/заморозка бізнесу: freeze_business, unfreeze_business, confiscate_business.
7. [x] API: 18 endpoints (/police/*, /court/*, /prison/*, /press/*, /lawyer/*).
8. [x] Тести: 18 passed (police, court, prison, press, lawyer). Full suite: 322 passed.

### Phase G9 — Casino, Atelier, Shadow Niches

1. [x] Казино як бізнес (blueprint `casino`, категорія `gambling`): блекджек + рулетка, rake 7%, house edge, податок 25%, ліцензійний збір 500/міс. Покер — створення/сетлмент (движок пізніше). `shut_down_casino` (відкликання ліцензії). Підпільне казино — через `shadow_service.open_shadow_business(type="illegal_casino")`.
2. [x] Ательє як бізнес (blueprint `atelier`, категорія `fashion`): створення скінів (JSON-конфіг), продаж (унікальні/масові), equip/unequip, list for sale. Commission 20% to atelier, tax 10% to treasury. Ціна: rarity × unique multiplier.
3. [x] Тіньові ніші: `criminal_rep` (add/decay/clamp 0-100), пропозиції шахрайства (шанс: <10=0%, 10-30=5%, 30-60=15%, 60-100=30%), accept/refuse, тіньовий ринок (buy 60%/sell 80% legal price, +2 rep), тіньові бізнеси (illegal_casino/smuggling/shadow_pharmacy/illegal_bar/money_laundering, доступ при rep>=30), check_discovery (chance=0.05+rep*0.003 → CorruptionLog), money_laundering_service (15% commission).
4. [x] Тести: 33 нових (8 casino, 8 atelier, 17 shadow). 355 total pass. `just check-g9` profile.

### Phase G10 — Education Tree, Exams, Licenses

1. [x] Освіта як дерево рішень: 8 курсів (economic, legal, police, medical, engineering, journalism, fashion, hospitality). Очно одна + заочно одна одночасно. Енергія: 1000/день (full_time), 500/день (part_time). Стипендія 50/день для очної.
2. [x] Іспити: take_exam (pass chance 0.7, -0.15 per fail), bribe_exam після 2 провалів (success = 0.5 + criminal_rep*0.005, cost 500). License validity 365 днів.
3. [x] Ліцензії: lawyer (legal education + exam), police (police education + exam), judge (legal education + exam), mayor eligibility (economic + legal + 90 successful_deals).
4. [x] Куплений диплом: buy_fake_diploma (cost 5000, +15 criminal_rep, is_fake=True, status=completed). expose_fake_diploma — НЕ блокує диплом, лише логування (per gameplay model).
5. [x] Стипендія від AI: 50/день для full_time (в daily_tick).
6. [x] Тести: 28 нових (8 enroll, 4 complete, 4 exams, 6 licenses, 5 fake diploma). 383 total pass. `just check-g10` profile.

### Phase G11 — 3D Visual Layers (Optional, post-G7)

1. [ ] Шейдери для сезонів (весна — зелені дерева, зима — сніг).
2. [ ] Шейдери для pollution (туман, жовтий відтінок).
3. [ ] Динамічне освітлення (crime_risk → темніше, happiness → ящиріше).
4. [ ] UI-редактор скінів на клієнті (Godot Control, прев'ю аватара в реальному часі).

### Phase G12 — Poker Engine (post-G9)

1. [ ] Texas Hold'em: колода, руки, банк, раунди (preflop/flop/turn/river), дії (fold/check/call/raise/all-in).
2. [ ] WebSocket real-time гра.
3. [ ] AI-гравці (NPC) з різними стилями (tight/loose/aggressive).
4. [ ] Тести.

## Open Debt Register

- `CityDashboardController.cs` зменшено до 502 рядків; presentation та API orchestration ізольовані у власних partial-ах.
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
- Наступний активний debt: Sprint 60 items 37-40 (клієнтський каркас — dashboard HUD, onboarding flow, visible city layer, business guidance).
- Audit cleanup завершено (commit `a7e0573`): missing db.commit() в /shadow/fraud-offer, atelier endpoints wired, httpx2 видалено, dotnet-format hook fixed, empty dirs cleaned.
- Test refactor завершено (commit `0cfba61`): shared conftest.py fixtures, named STARTER_*_COUNT constants, wire police refuse_bribe/confiscate_business + press accept_advertising, module-level imports в mvp.py, frozen models docs, confiscate_business bugfix.
- Observability metrics fix: `ces_http_requests_total` / `ces_http_request_duration_seconds` перенесено з `observability.py` в `metrics.py` — `/metrics` endpoint тепер експортує кастомні метрики без залежності від app startup.
- G6-G10 day tick integration завершено: police auto-patrol, press investigation tick, shadow business income + discovery + fraud offers + monthly criminal_rep decay, education daily energy/scholarship + auto-completion. `phase_g6_to_g10_tick.py` module, defensive (no-op if no records). 10 integration tests, `just check-g-integration` profile.
- Post-MVP gameplay design завершено (Round 1-14, `GAMEPLAY_CORE_MODEL.md` розділи 13-29). Витягнуто у Phase G1-G12 нижче. Активна фаза: G1 (Dynamic District Metrics).
- Test workflow оптимізований через `scripts/check_targeted.ps1` і `just check-*`; це default dev loop. Full gate лишається фінальною перевіркою, а не основним способом ітерації.

## Progress Snapshot

- Phase 0 — Dev Foundation: 100%
- Phase 1 — 5-Minute Core Loop: 100%
- Phase 2 — Architecture Split: 100%
- Phase 3 — Economy Balance: 82%
- Phase 4 — Godot MVP Client: 75%
- Phase 5 — Multiplayer Readiness: 90%
- Phase 6 — Production Ready: 99%
- Phase G1 — Dynamic District Metrics: 100% (DONE)
- Phase G2 — NPC Residents: 100% (DONE)
- Phase G3 — Utility Services: 100% (DONE)
- Phase G4 — Vacancies and Hiring: 100% (DONE)
- Phase G5 — Bank as Business: 100% (DONE)
- Phase G6 — Political System: 100% (DONE)
- Phase G7 — 3D Avatar and Locations: 100% (DONE)
- Phase G8 — Prison/Police/Press/Court/Lawyer: 100% (DONE, backend)
- Phase G9 — Casino/Atelier/Shadow Niches: 100% (DONE, backend)
- Phase G10 — Education Tree/Exams/Licenses: 100% (DONE, backend)
- Phase G11 — 3D Visual Layers: 0%
- Phase G12 — Poker Engine: 0%

## Verified Now

- Backend tests: `393 passed / 0 failed`.
- Client logic tests: passed; Godot C# build: passed, 0 warnings/errors.
- Controller split: main controller — 502 рядки; API dispatch, presentation, guided actions і feature routing рознесені по partial-ах.
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

- sports, cartels, unions, insurance, advanced routes.
- Shadow economy — розморожено як частину Post-MVP Gameplay Phases (G8-G9: corruption, prison, shadow niches).
- Нові системи не брати, поки current queue не закрита і 5-minute loop не відчувається стабільним.
- Post-MVP Gameplay Phases: G1-G10 завершено (backend); G11-G12 (3D visual layers, poker engine) — optional, post-MVP. Активна черга: Sprint 60 client polish (items 37-40).

## Reference Inputs

- Gameplay north star: `GAMEPLAY_CORE_MODEL.md`
- Tool inventory: `TOOLS.md`
- User-facing overview: `README.md`

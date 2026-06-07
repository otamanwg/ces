# Solo Working Roadmap — City Economic Simulator

Цей файл — робочий план для щоденного руху. Він важливіший за великий vision-roadmap, коли треба вибрати наступну задачу.

Проект ведеться малими перевіреними шматками. Якщо наступний крок очевидний, Codex продовжує сам: backend + tests first, потім Godot/client, `scripts/check.ps1` перед завершенням. Питати користувача тільки при архітектурному конфлікті або якщо тести падають після 2 спроб.

---

## Поточний Стан

### Готово

- PostgreSQL-only backend з Alembic.
- FastAPI MVP routes: city, player, jobs, work, sleep, exam.
- Єдиний API envelope: `success`, `message`, `data`, `effects`.
- Player auth token для state-changing player routes.
- Idempotency для `work`, `sleep`, `exam`.
- Godot 4.3 .NET client, C# build зелений.
- Godot MCP addon + локальний Python bridge для Codex/Cursor.
- Dashboard scroll-wrapper для мобільного viewport.
- `scripts/check.ps1` як головний checkpoint.

### Поточний Фокус

**Sprint 49: Anime Visual Direction.**

Мета: підготувати оригінальний аніме-пак із візуальною мовою, натхненою The Legend of Neverland, але адаптованою до сучасного міста й SimCity 4 Deluxe-подібної камери.

Core gameplay direction зафіксований у `GAMEPLAY_CORE_MODEL.md`: місто-сервер живе 24/7, старт через автобусний вокзал, земля/будівництво через мерію і біржу, переїзд між містами доступний одразу з логістичними обмеженнями.

### Майбутні Visual Style Packs

Гра має підтримувати кілька візуальних стилів за вподобанням гравця: `anime`, `hyperreal`, `mafia` або інші тематичні паки. Першим повним альтернативним паком буде `anime`; The Legend of Neverland використовується як орієнтир для загальної мови рендерингу, а не як джерело персонажів чи асетів.

Архітектурний принцип: style pack змінює тільки presentation layer — фон, палітру, портрети, іконки, VFX, звуки та шрифтовий настрій. Економічні механіки, API contracts, player progression, balance і backend simulation залишаються спільними для всіх стилів.

Поки MVP loop не відчувається як гра, основний стиль — нейтральний `core`, а всі scene/node names і client presenters мають лишатися style-agnostic.

---

## Definition Of Done

Кожна задача вважається завершеною тільки якщо:

- Backend tests проходять.
- `scripts/check.ps1` проходить.
- Якщо змінювалась сцена або Godot code: `get_errors` через MCP повертає `0 error(s)`.
- Зміни закомічені окремим зрозумілим commit message.
- Немає критичних TODO для цієї ж задачі.

---

## Правила Руху

1. Один commit = одна причина.
2. Backend contract + tests перед UI.
3. Не додавати нові системи, поки MVP loop не відчувається стабільним.
4. Не перетирати зміни користувача/Cursor: перед роботою `git status`.
5. Якщо Codex бачить очевидний наступний крок, він бере його сам.
6. Якщо задача зачіпає сцени, використовувати Godot MCP.
7. Перед фінальним повідомленням запускати `scripts/check.ps1`.

---

## Autonomous Execution Queue

Це черга, яку Codex виконує без додаткового підтвердження, поки немає архітектурного конфлікту або повторного падіння тестів.

1. Брати перший незакритий пункт активного sprint.
2. Написати або оновити regression test.
3. Реалізувати мінімальний fix.
4. Запустити targeted tests.
5. Запустити `scripts/check.ps1`.
6. Якщо є Godot/client зміни: перевірити Godot MCP `get_errors`.
7. Оновити статус у цьому roadmap, якщо пункт закритий.
8. Зробити commit.
9. Перейти до наступного пункту черги.

Зупинка потрібна тільки якщо:

- потрібне продуктове рішення між двома різними gameplay-напрямками;
- зміна ламає існуючу архітектуру або потребує схеми БД;
- tests/check падають після 2 спроб;
- користувач прямо каже зупинитись або переключитись.

---

## Sprint 5 — MVP Hardening (поточний)

Ціль: прибрати неочевидні поломки core loop, вирівняти API-помилки, зробити клієнт стійким до поганого стану.

| # | Задача | Статус | Перевірка |
|---|--------|--------|-----------|
| 5.1 | Invalid session на `jobs/apply` повертає session error | ✅ | `test_api_mvp_loop.py` |
| 5.2 | Malformed IDs не дають 500 у auth/apply flow | ✅ | `test_api_mvp_loop.py` |
| 5.3 | Повторний college exam не списує гроші вдруге | ✅ | `test_api_mvp_loop.py` |
| 5.4 | Перевірити malformed IDs для `work/sleep/exam` routes | ✅ | `test_api_mvp_loop.py` |
| 5.5 | Уніфікувати user-facing error messages для core actions | ✅ | API tests + client status |
| 5.6 | Перевірити idempotency edge cases: same key, wrong player/action | ✅ | service/API tests |
| 5.7 | Перевірити money/ledger consistency після work/sleep/exam | ✅ | transaction tests |

Після кожного пункту: `scripts/check.ps1`, commit.

---

## Sprint 6 — Godot UX Polish

Ціль: перша 5-хвилинна петля має читатися як гра, не як debug dashboard.

Порядок:

1. ✅ Status/effects history: останні 3-5 подій після дій гравця.
2. ✅ Чіткі loading/busy стани для кнопок під час API-запиту.
3. ✅ Error states: backend unavailable, invalid session, no vacancies, insufficient energy.
4. ✅ Mobile layout pass: 360x640 і 720x1280 без обрізання тексту.
5. ✅ Exam panel polish: варіанти відповідей, disabled submit без відповіді, результат після складання.
6. ✅ Playtest smoke через Godot MCP run_scene + `get_errors`; `-ResetDb` лишити для ручного чистого прогону.

DoD:

- Godot MCP `get_errors` = 0.
- Client build проходить.
- Візуальний smoke screenshot після зміни сцени.

---

## Sprint 7 — Balance & 5-Minute Feel

Ціль: MVP loop має бути не тільки правильним, а й відчутно нормальним по темпу.

Порядок:

1. ✅ Зафіксувати target loop: старт не може скласти іспит, після 1 work + 1 sleep вже може.
2. ✅ Налаштувати exam cost під target loop: 650 ₴ при старті 500 ₴.
3. ✅ Додати balance tests: гравець може пройти loop без grind і без infinite money.
4. ✅ Перевірити `next_action` після кожного кроку.
5. ✅ Оновити README з очікуваним dev playtest сценарієм.

---

## Sprint 8 — Architecture Cleanup

Ціль: підготувати код до наступних систем без великого переписування.

Порядок:

1. ✅ Винести повторювані player/job/city queries у repositories або focused service helpers.
2. ✅ Переглянути прямі money mutations, де потрібен ledger/debit/credit helper.
3. ✅ Додати route-level DTO там, де зараз сирі dict-структури.
4. ✅ Зменшити відповідальність `CityDashboardController.cs`, якщо UI стане важким.

Не робити це наперед: тільки після Sprint 5-7 або коли зміна реально спрощує наступний крок.

---

## Sprint 9 — Food / Basic Needs

Ціль: додати просту потребу, яка впливає на щоденний цикл, не ламаючи `work -> sleep -> exam -> better job`.

Порядок:

1. ✅ Backend: `Player.hunger`, Alembic migration, зростання голоду від work/sleep/day tick.
2. ✅ Backend: `eat` action, ledger `food`, idempotent API endpoint.
3. ✅ Tests: service/API/player progress coverage для hunger/eat.
4. ✅ Client: HungerBar + кнопка “Поїсти” у dashboard.
5. ⏳ Перевірка: `scripts/check.ps1`, Godot MCP `get_errors`, commit.

Наступні кандидати після закриття Sprint 9:

1. Simple business ownership.
2. City events/news.
3. Sports as lightweight side progression.

---

## Sprint 10 — Simple Business Ownership

Ціль: додати перший MVP-шлях “заробив гроші -> купив малий бізнес” без повної симуляції компаній.

Порядок:

1. ✅ Backend: buyable seed business, market listing, purchase service.
2. ✅ Backend: ownership snapshot/actions/effects, ledger `business_purchase`.
3. ✅ Tests: service/API/idempotency coverage для купівлі бізнесу.
4. ✅ Client: показ власного бізнесу + кнопка “Купити бізнес”.
5. ✅ Backend/client: owner dividend action із каси бізнесу.
6. ⏳ Перевірка: `scripts/check.ps1`, Godot MCP `get_errors`, commit.

Наступний вузький крок після Sprint 10:

1. City events/news.
2. Sports as lightweight side progression.

---

## Sprint 11 — City Events / News

Ціль: показувати гравцю короткі події міста з реального стану системи.

Порядок:

1. ✅ Backend: generated city news для `/api/city/status`.
2. ✅ Backend: day tick news для `/api/city/tick-day`.
3. ✅ Tests: API/service coverage для news payload.
4. ✅ Client: додавати `news[]` в історію подій dashboard.
5. ⏳ Перевірка: `scripts/check.ps1`, Godot MCP `get_errors`, commit.

Наступний вузький крок після Sprint 11:

1. Sports as lightweight side progression.
2. News polish/filtering, якщо feed стане шумним.

---

## Sprint 12 — Sports Side Progression

Ціль: зробити спорт маленькою додатковою петлею: вступ у клуб -> тренування -> stats.

Порядок:

1. ✅ Backend: MVP sports clubs endpoint.
2. ✅ Backend: authenticated/idempotent join sports club.
3. ✅ Backend: authenticated/idempotent gym training із ledger `gym_training`.
4. ✅ Tests: service/API money, energy, idempotency, sports actions.
5. ✅ Client: sport status + кнопки “У спорт” і “Тренуватись”.
6. ⏳ Перевірка: `scripts/check.ps1`, Godot MCP `get_errors`, commit.

Наступний вузький крок після Sprint 12:

1. ✅ Sports match payout smoke.
2. ✅ Economy audit: private/public ledger coverage for remaining frozen systems.
3. News polish/filtering, якщо feed стане шумним.

Поки не чіпати:

- Cartels.
- Shadow economy як основний loop.
- Full politics.
- Full insurance/unions.
- Mobile export/release.

---

## Sprint 13 — Frozen Economy Audit

Ціль: side-системи, які ще не стали основним loop, не повинні ламати бухгалтерію MVP.

Порядок:

1. ✅ Backend: fake diploma purchase логувати як shadow/system money sink.
2. ✅ Backend: police audit стягує тільки доступний баланс і не створює повний штраф у treasury.
3. ✅ Backend: insurance premiums, loan repayments, collector seizure, lobby fund transfers використовують `debit`/`credit`.
4. ✅ Tests: frozen economy coverage для дипломів, страхування, кредитів/колекторів.
5. ✅ Перевірка: `scripts/check.ps1`, commit.

Наступний вузький крок після Sprint 13:

1. ✅ News polish/filtering, якщо feed стане шумним.
2. ✅ API/client presentation pass для sports/news.
3. ✅ Ще один ledger audit, якщо знайдуться прямі money mutations поза services.

---

## Sprint 14 — Client Controller Hardening

Ціль: dashboard controller має лишатися керованим, поки MVP обростає кнопками й панелями.

Порядок:

1. ✅ Client: винести action button state у `DashboardActionPresenter`.
2. ✅ Client: винести parsing/formatting player snapshot у focused presenter/model.
3. ⏭️ Client: lightweight smoke для status/history formatting відкласти до появи C# test runner.
4. ✅ Перевірка: `scripts/check.ps1`, Godot MCP `get_errors`, commit.

Наступний вузький крок після Sprint 14:

1. ✅ Backend/API contract pass для player snapshot DTO.
2. ✅ Manual playtest pass через `scripts/play.ps1 -ResetDb -RunCheck`.
3. Route envelope DTO pass для city status/news.

---

## Sprint 15 — API Contract Hardening

Ціль: основні відповіді MVP мають проходити через Pydantic DTO перед тим, як їх споживає Godot client.

Порядок:

1. ✅ Backend: `PlayerSnapshotData`, `PlayerActionsData`, business/sports snapshot DTO.
2. ✅ Tests: validated player snapshot contract із job/hostel/business/sports/actions.
3. ✅ Backend: city status/news DTO.
4. ✅ Tests: API contract coverage для city status/news.
5. ✅ Перевірка: `scripts/check.ps1`, commit.
6. ✅ Manual smoke: Godot MCP `run_scene` + HTTP `scripts/smoke_mvp.py`.
7. ✅ Tests: DTO contract coverage для vacancies/business market/sports clubs/exam info.
8. ✅ Backend/tests: DTO contract coverage для action responses.
9. ✅ Backend: helper для player action responses + idempotency save.
10. ✅ Backend: винести action response helper-и з route file в `api/responses.py`.
11. ✅ Backend/tests: service result DTO для business purchase/dividend.
12. ✅ Backend/tests: service result DTO для meal/sports training/exam submit.
13. ✅ Backend/tests: service result DTO для work/sleep/day tick.
14. ✅ Backend/tests: service result DTO для sports contract/match simulation.
15. ✅ Backend/tests: service result DTO для frozen economy diploma/audit/insurance/loans.
16. ✅ Backend/tests: service result DTO для union strike/lobby fund.
17. ✅ Backend/tests: frozen sports simulate route response DTO.
18. ✅ Client/Godot smoke: dashboard scene запускається, city status API 200, MCP errors 0.
19. ✅ Backend/API: frozen routes винесено в `/api/frozen`, MVP `/api` перевірено проти колізій.
20. ✅ Backend/tests: frozen sports clubs route response DTO.

---

## Sprint 16 — Client Testability & UX Guards

Ціль: client presenter/parser логіка має мати швидкі regression tests поруч із backend checks.

Порядок:

1. ✅ Client/tests: lightweight C# console test runner для `DashboardEventHistory`.
2. ✅ Client/tests: action presenter state matrix без Godot runtime через `DashboardActionViewModel`.
3. ✅ Client/tests: player snapshot parser smoke без Godot runtime.
4. ✅ Client/Godot smoke після client script змін: dashboard scene, city status 200, MCP errors 0.

---

## Sprint 17 — Dev Recovery & Smoke Reliability

Ціль: локальна розробка після перезапуску ПК має швидко повертатися в робочий стан без ручного піднімання кількох процесів.

Порядок:

1. ✅ Scripts: `start_backend.ps1` із health-check, logs і background start.
2. ✅ Scripts: `play.ps1` використовує backend starter замість ad-hoc PowerShell window.
3. ✅ Scripts: `dev.ps1` стартує backend і запускає HTTP MVP smoke.
4. ✅ Scripts: one-command Godot MCP bridge + dashboard smoke wrapper.

---

## Sprint 18 — Playtest Readiness

Ціль: ручний 5-хвилинний playtest має мати зрозумілий сценарій, reset/start команди і критерії “готово/не готово”.

Порядок:

1. ✅ Docs/scripts: playtest checklist для `work -> sleep -> exam -> sports/business`.
2. ✅ Scripts: console output для playtest старту в `play.ps1`.
3. ✅ Client: disabled action tooltips пояснюють, чому дія недоступна.
4. ✅ Перевірка: `check.ps1`, `smoke_godot_dashboard.ps1`, commit.

---

## Sprint 19 — Core Visual Model

Ціль: базовий Godot-клієнт має виглядати як landscape-first game screen, а не вертикальний бухгалтерський dashboard.

Порядок:

1. ✅ Project/client: landscape viewport `1280x720`.
2. ✅ Scene: три зони `player/city status -> city visual -> actions`.
3. ✅ Assets: neutral `core` city backdrop замість тимчасових прямокутників.
4. ✅ Scene: підключити core asset так, щоб майбутній style pack міг підмінити тільки visual layer.
5. ✅ Text safety: перевірити довгі job/status/event strings у landscape без вильоту за контейнер.
6. ✅ Перевірка: `check.ps1`, `smoke_godot_dashboard.ps1`, commit.

---

## Sprint 20 — City District Foundation

Ціль: перетворити місто з одного абстрактного статусу на набір районів із метриками, які згодом керуватимуть візуалом, землею, AI-мером, медициною, криміналом і цінами.

Порядок:

1. ✅ Backend: `CityDistrict` model/table + Alembic migration.
2. ✅ Backend: 6 стартових районів для малого міста: вокзал, комерційне ядро, висотна житлова зона, промзона, передмістя, зовнішні землі.
3. ✅ Backend: district metrics у `/api/city/status`: rent, jobs, crime, traffic, services, medicine, land value, desirability.
4. ✅ Tests: seed/API contract coverage для стартових районів.
5. ✅ Docs: зафіксувати правила AI-мера, debt recovery, onboarding age adaptation і 24h move cooldown.
6. ✅ Backend/tests: rule-based AI mayor policy для майбутніх building applications.
7. ⏳ Наступний backend крок: `BuildingApplication` або `LandParcel` skeleton.

---

## Sprint 21 — Land And Building Applications

Ціль: перетворити районний шар на першу реальну економічну одиницю землі та підготувати будівництво через AI-мера.

Порядок:

1. ✅ Backend: `LandParcel` model/table + Alembic migration.
2. ✅ Backend: стартові city-owned ділянки, прив'язані до 6 районів.
3. ✅ Backend/API: `/api/land/parcels` повертає доступні parcel-и з district context і ціною.
4. ✅ Backend: `BuildingApplication` model/table.
5. ✅ Backend/API: authenticated `/api/building/applications`, idempotent submit.
6. ✅ Backend: заявка можлива тільки на власну ділянку.
7. ✅ Backend/tests: AI mayor policy інтегровано в building application response.
8. ✅ Backend/API/tests: land purchase з ledger `land_purchase`, ownership transfer і перевіркою балансу.
9. ⏳ Наступний backend крок: approved building application activation у building/asset record.

---

## Sprint 22 — Building Activation

Ціль: погоджена AI-мером заявка має стати реальним міським активом, який згодом можна буде показувати на карті й включати в економіку.

Порядок:

1. ✅ Backend: визначити мінімальну `Building`/asset model.
2. ✅ Backend: activation endpoint тільки для `approved` applications.
3. ✅ Backend: parcel status переходить із `owned` у `built`.
4. ✅ Backend/tests: approved/revision/ownership/idempotency coverage.
5. ✅ Backend: `Building` стартує як `built` + `inactive`.

---

## Sprint 23 — Building Operations

Ціль: будівля після activation має мати зрозумілий шлях до операційної економіки, але без включення повної симуляції одразу.

Порядок:

1. ✅ Backend: endpoint для opening/activation operating status.
2. ✅ Backend/API/tests: opening fee з ledger `building_opening_fee`.
3. ✅ Backend: commercial building створює linked `shop` business.
4. ✅ Backend: industrial building створює linked `factory` business.
5. ✅ Backend/tests: ownership, status transition, ledger, idempotency coverage.
6. ✅ Наступний backend крок перед upkeep: винести business choices у blueprint catalog.

---

## Sprint 24 — Business Blueprint Catalog & Metrics

Ціль: гравець має відкривати бізнес із зрозумілого каталогу, а backend має використовувати один source-of-truth для типу бізнесу, типу забудови, opening fee, ризиків і city metric effects.

Порядок:

1. ✅ Backend: `BusinessBlueprint` model/table + Alembic migration.
2. ✅ Backend: starter catalog із 7 бізнесів: кіоск, кав'ярня, міні-маркет, майстерня, хостел, аптека, мала фабрика.
3. ✅ Backend/API: `/api/business/blueprints` повертає опис, вартість, profit range, ризики, allowed land/zoning, metric effects і visual tags.
4. ✅ Backend: `BuildingApplication` приймає `business_blueprint_id`, валідує ділянку і бере метрики з blueprint замість клієнтських цифр.
5. ✅ Backend: activation копіює blueprint у `Building`.
6. ✅ Backend: opening бере `opening_fee` і linked `Business.type` з blueprint, fallback лишається для legacy/manual заявок.
7. ✅ Backend/tests: seed/API/application/opening coverage для blueprint і metric source-of-truth.
8. ✅ Наступний backend крок визначено: мінімальний daily upkeep для active buildings на основі `upkeep_daily`.

---

## Sprint 25 — Building Upkeep & Passive Cashflow Guards

Ціль: активна player-built будівля не має бути безкоштовним вічним активом. Вона повинна мати легку щоденну вартість утримання, яка пізніше стане основою для прибутковості, банкрутства, аукціонів і керуючих компаній.

Порядок:

1. ✅ Backend: визначити MVP правило upkeep для `Building.operating_status = active`.
2. ✅ Backend: списувати `upkeep_daily` з linked business cash або власника за безпечним правилом.
3. ✅ Backend: якщо upkeep не сплачено, переводити будівлю у м'який проблемний стан без миттєвого знищення активу.
4. ✅ Backend/tests: day tick coverage для active building upkeep, недостатніх коштів і ledger.
5. ✅ Docs: описати, як upkeep переходить у майбутні правила банкрутства/аукціону.
6. ⏳ Наступний backend крок: repair/reopen endpoint для `maintenance_due`.

---

## Sprint 26 — Building Repair/Reopen Path

Ціль: `maintenance_due` має бути зрозумілим тимчасовим станом, а не пасткою. Гравець повинен бачити, скільки треба сплатити, і мати дію для повернення будівлі в `active`.

Порядок:

1. ✅ Backend: визначити repair fee для `maintenance_due` building.
2. ✅ Backend/API: authenticated repair/reopen endpoint тільки для власника.
3. ✅ Backend: ledger purpose `building_repair_fee`.
4. ✅ Backend/tests: owner/status/money/idempotency coverage.
5. ✅ Client later: показ проблемної будівлі й кнопка ремонту.
6. ✅ Наступний backend крок: building portfolio API для власних будівель.

---

## Sprint 27 — Building Portfolio API & Client Prep

Ціль: створити контракт, з якого Godot зможе показати гравцю його ділянки/будівлі, активний/проблемний стан, repair fee і наступну дію.

Порядок:

1. ✅ Backend/API: authenticated endpoint для списку будівель гравця.
2. ✅ Backend DTO: building + blueprint summary + opening/repair fee + available actions.
3. ✅ Backend/tests: owner-only, status/action matrix, DTO validation.
4. ✅ Client: мінімальний read-only блок "Мої будівлі" у dashboard.
5. ✅ Client: repair/open button тільки коли API повертає відповідну `available_actions`.

---

## Sprint 28 — Godot Building Portfolio Panel

Ціль: dashboard має показувати не тільки баланс і кнопки core loop, а й перший фізичний слід гравця в місті: його будівлі.

Порядок:

1. ✅ Client: API method для `GET /api/player/{player_id}/buildings`.
2. ✅ Client: parser/model для `BuildingPortfolioData`.
3. ✅ Client: компактний read-only panel у landscape dashboard.
4. ✅ Client: open/repair buttons за `available_actions`.
5. ✅ Client tests: parser/action presenter coverage.
6. ✅ Godot MCP smoke: scene без Diagnostics errors.

---

## Sprint 29 — Player Building Creation Flow

Ціль: дати гравцю перший шлях до фізичної будівлі на сервері без ручного seed/debug сценарію.

Порядок:

1. ✅ Backend/API audit: перевірити існуючі endpoints землі, blueprints, заявок і activation.
2. ✅ Backend/tests: додати наскрізний smoke `land purchase -> blueprint application -> approval -> activation -> portfolio`.
3. ✅ Client model/parser: starter land options і blueprint catalog presenter.
4. ✅ Client UI: компактний "Побудувати" flow у dashboard без перевантаження основного екрану.
5. ✅ Client action: buy recommended starter parcel.
6. ✅ Client action: submit blueprint application for owned starter land.
7. ✅ Client action: activate approved building.
8. ✅ Godot MCP smoke + `scripts/check.ps1` + commit.

---

## Sprint 30 — Core City Visual Layer

Ціль: перетворити центральний visual panel на читабельну карту міста-сервера, прив'язану до реальних district metrics і building portfolio.

Порядок:

1. ✅ Client model: `DashboardCityVisualModel` для city districts і building counts.
2. ✅ Godot scene: `CityVisualOverlay` поверх core backdrop.
3. ✅ Controller wiring: `/api/city/status` оновлює райони, portfolio оновлює активи гравця.
4. ✅ Client tests: district parsing, pressure score, headline, portfolio counts.
5. ✅ Godot MCP smoke + `scripts/check.ps1` + commit.

Наступний visual крок після Sprint 30:

1. ✅ Building archetype markers: kiosk, coffee, hostel, pharmacy, workshop, factory.
2. ✅ Видимий стан будівлі: inactive/active/maintenance_due.
3. ⏳ Легке zoom-перемикання між overview і street-focus без зміни backend mechanics.

---

## Sprint 31 — Building Archetype Markers

Ціль: portfolio має передавати візуальному шару не тільки кількість будівель, а й тип, район і стан кожного активу.

Порядок:

1. ✅ Client parser: `DashboardBuildingItem` зберігає `district_code`, `blueprint_code`, `project_type`.
2. ✅ Visual model: `DashboardCityVisualBuilding` і archetype label.
3. ✅ Godot overlay: окремі маркери будівель з кольором archetype і рамкою стану.
4. ✅ Client tests: parser fields і visual building mapping.
5. ✅ Godot MCP smoke + `scripts/check.ps1` + commit.

Наступний visual крок після Sprint 31:

1. ✅ Overview/street-focus toggle.
2. ⏳ Легка анімація міського шару без зміни gameplay state.
3. ⏳ Підготовка style-token palette для майбутніх visual packs.

---

## Sprint 32 — Overview / Street Focus Toggle

Ціль: центральна visual panel має перемикатися між картою районів і ближчим street-focus шаром, щоб майбутній zoom не вимагав переписування сцени.

Порядок:

1. ✅ `CityVisualOverlay`: focus mode і street-focus drawing.
2. ✅ Scene: кнопка `VisualFocusButton` у visual panel.
3. ✅ Controller: handler перемикає режим overlay і текст кнопки.
4. ✅ Godot MCP smoke + `scripts/check.ps1` + commit.

Наступний visual крок після Sprint 32:

1. ✅ Легка idle-анімація overlay: traffic pulse, asset attention pulse.
2. ✅ Style-token palette для майбутніх visual packs.
3. ✅ Підготовка screenshot/playtest script для швидкого показу результату.

---

## Sprint 33 — City Idle Animation

Ціль: карта має виглядати живою навіть без дій гравця, але анімація не повинна впливати на simulation state або перевантажувати слабкі пристрої.

Порядок:

1. ✅ Client logic: детерміновані `pulse` і `travel` helpers з regression tests.
2. ✅ Godot overlay: рух трафіку на overview і street-focus.
3. ✅ Godot overlay: attention pulse для активів, що потребують ремонту.
4. ✅ Performance guard: redraw не частіше 20 FPS.
5. ✅ Godot MCP smoke + `scripts/check.ps1` + commit.

---

## Sprint 34 — Visual Style Tokens

Ціль: закласти palette contract для майбутніх стилів без додавання перемикача в незавершений MVP UI.

Порядок:

1. ✅ Client model: registry `core`, `anime`, `hyperreal`, `mafia` з безпечним fallback на `core`.
2. ✅ Client tests: code normalization, fallback і token behavior.
3. ✅ Godot overlay: фон, дороги, трафік, текст і status colors використовують semantic tokens.
4. ✅ Godot MCP smoke + `scripts/check.ps1` + commit.

Наступний visual крок після Sprint 34:

1. ✅ Підготовка screenshot/playtest script для швидкого показу результату.
2. Збереження visual style preference у player session.
3. UI selector додавати лише після готовності першого повного alternative asset pack.

---

## Sprint 35 — Visual Capture Automation

Ціль: одна команда має зібрати client, підняти backend, відкрити службову capture-сцену і зберегти валідний PNG `1280x720`.

Порядок:

1. ✅ Godot tool scene: dashboard capture runner з очікуванням API/render.
2. ✅ Script: `scripts/capture_dashboard.ps1` з output path і PNG validation.
3. ✅ Docs: команда швидкого visual QA.
4. ✅ Реальний screenshot + Godot MCP errors 0 + `scripts/check.ps1` + commit.

---

## Sprint 36 — Visual Style Preference

Ціль: style code має переживати перезапуск клієнта і завжди проходити через allowlist/fallback, навіть до появи selector UI.

Порядок:

1. ✅ Client session: `VisualStyleCode` із fallback на `core`.
2. ✅ Controller: застосувати session preference до `CityVisualOverlay`.
3. ✅ Client tests: normalization/fallback contract.
4. ✅ Godot MCP smoke + `scripts/check.ps1` + commit.

---

## Sprint 37 — Landscape Text Safety

Ціль: довгі локалізовані рядки не виходять за межі rail/panel, не перекривають сусідні controls і не змінюють стабільну ширину dashboard.

Порядок:

1. ✅ Capture tool: `-StressText` для реалістичних довгих player/status/building strings.
2. ✅ Visual QA: screenshot `1280x720` і фіксація фактичних переповнень.
3. ✅ Scene/client fixes: wrapping, clipping або overrun тільки у проблемних вузлах.
4. ✅ Повторний screenshot + Godot MCP smoke + `scripts/check.ps1` + commit.

---

## Sprint 38 — Player Arrival Vertical Slice

Ціль: перший керований момент гри має бути сюжетним, збереженим на сервері та обов'язковим перед економічними діями.

Порядок:

1. ✅ PostgreSQL: `player_onboarding`, Alembic backfill для існуючих гравців.
2. ✅ Backend: стартові 300–400 ₴, вибір поліція/житло, відкладене часткове повернення коштів.
3. ✅ Backend guards/tests: core actions заблоковані до поселення; idempotency і ledger покриті.
4. ✅ Client: style-agnostic arrival presenter та модальний landscape overlay, створений через Godot MCP.
5. ✅ Visual QA: `capture_dashboard.ps1 -Onboarding`, Godot MCP smoke, повний checkpoint.

Наступний крок:

1. Sprint 40: окремий візуальний шар автовокзалу та короткі діалогові beats до моменту крадіжки.

---

## Sprint 39 — Police Recovery Follow-up

Ціль: відкладений результат заяви до поліції має повертатися у видимий і завершуваний gameplay loop.

Порядок:

1. ✅ Backend snapshot: серверний `police_recovery_claimable` з перевіркою реального часу.
2. ✅ Backend tests: due recovery стає доступним і після claim більше не пропонується.
3. ✅ Client: контекстна кнопка із сумою, idempotent claim і автоматичне приховування після виплати.
4. ✅ Visual QA: окремий `-PoliceRecovery` capture state без переповнення landscape rail.

---

## Sprint 40 — Arrival Visual Narrative

Ціль: вступ має виглядати як ігрова сцена, а не як текстовий modal поверх dashboard.

Порядок:

1. ✅ Imagegen core asset: landscape-автовокзал, гравець із телефоном, таксі з викраденим багажем.
2. ✅ Godot MCP: окремий `OnboardingBackdrop` під сюжетною панеллю.
3. ✅ Client: три короткі story beats і кнопка `Далі` перед фінальним вибором.
4. ✅ Capture workflow: `-ArrivalStory` і повторна перевірка фінального choice screen.
5. ✅ Повний checkpoint, MCP smoke і commit.

Наступний visual крок:

1. Локалізувати фінальний choice screen і police recovery controls.
2. Додати character-creation screen, де гравець свідомо обирає tutorial age group.

---

## Sprint 41 — Arrival Style-Pack Assets

Ціль: story beat обирає семантичний visual key, а style pack підставляє свій ресурс із безпечним fallback на `core`.

Порядок:

1. ✅ Client architecture: manifest для `core`, `anime`, `hyperreal`, `mafia` та fallback без розгалужень у gameplay-коді.
2. ✅ Imagegen core assets: окремий зал очікування та поїздка в таксі.
3. ✅ Godot runtime: перемикання `OnboardingBackdrop` відповідно до story beat.
4. ✅ Visual QA: окремі capture states для waiting hall, taxi ride і фінального choice screen.
5. ✅ Повний checkpoint, MCP smoke і commit.

---

## Sprint 42 — Localized Arrival Narrative

Ціль: C# runtime і GDScript capture tooling використовують ті самі translation keys, а story model більше не містить display text.

Порядок:

1. ✅ Godot translation catalog: українська базова та англійська перевірочна локаль.
2. ✅ Client model: story beats містять `TitleKey`, `NarrativeKey` і semantic visual key.
3. ✅ Runtime/capture: текст і кнопки вступу проходять через `Tr(...)` / `tr(...)`.
4. ✅ Tests і visual QA для української та англійської локалі.
5. ✅ Повний checkpoint, MCP smoke і commit.

---

## Sprint 43 — Arrival NPC Portrait Layer

Ціль: story beat визначає semantic portrait і сторону екрана, а style pack підставляє конкретний NPC asset.

Порядок:

1. ✅ Imagegen core assets: співрозмовник автовокзалу та водій таксі.
2. ✅ Client architecture: portrait keys, side metadata і fallback у style-pack manifest.
3. ✅ Godot MCP/runtime: окремий `OnboardingPortrait`, позиціонування та приховування на choice screen.
4. ✅ Localized visual QA для waiting hall, taxi ride і фінального вибору.
5. ✅ Повний checkpoint, MCP smoke і commit.

---

## Sprint 44 — Age-Aware Arrival Guidance

Ціль: профіль зберігає лише потрібну для tutorial вікову групу, а другий вступний beat адаптує тон українською й англійською.

Порядок:

1. ✅ PostgreSQL: `players.tutorial_age_group` з migration, default і check constraint.
2. ✅ Backend API/tests: `teen`, `adult`, `mature`, legacy-compatible default і snapshot contract.
3. ✅ Client: parser профілю та age-aware narrative key без зміни story sequence.
4. ✅ Visual QA для teen/adult/mature локалізованих підказок.
5. ✅ Повний checkpoint, MCP smoke і commit.

---

## Sprint 45 — Localized Arrival Choice And Recovery

Ціль: фінальний вибір вступу, статус заяви та отримання повернених коштів використовують semantic translation keys із backend text fallback.

Порядок:

1. ✅ Client state: stage/status перетворюються на стабільні localization keys.
2. ✅ Runtime/capture: choice buttons, pending states і recovery amount локалізовані.
3. ✅ Godot MCP: editor defaults замінені на translation keys.
4. ✅ Visual QA українською та англійською для choice/recovery states.
5. ✅ Повний checkpoint, MCP smoke і commit.

Наступний visual крок:

1. Додати character-creation screen, де гравець свідомо обирає tutorial age group.

---

## Sprint 46 — Character Creation Bootstrap

Ціль: нова сесія більше не створює випадкового гравця автоматично; гравець вводить ім'я та обирає вікову групу персонажа перед arrival story.

Порядок:

1. ✅ Backend/tests: єдиний username contract 2–24 символи та збереження tutorial age group.
2. ✅ Client model: normalization/validation без залежності від Godot UI.
3. ✅ Godot MCP: landscape character-creation overlay з name input і трьома age-group сегментами.
4. ✅ Runtime: bootstrap чекає submit, обробляє duplicate/transport errors і запускає arrival flow.
5. ✅ Localized capture QA, повний checkpoint, MCP smoke і commit.

---

## Sprint 47 — First-Launch Language Preference

Ціль: гравець обирає українську або англійську до створення персонажа, а локальна сесія відновлює вибір при наступному запуску.

Порядок:

1. ✅ Client model/tests: locale allowlist і deterministic fallback.
2. ✅ Game session: збереження locale до та після створення персонажа.
3. ✅ Godot MCP/runtime: компактний `UK / EN` selector на character-creation screen.
4. ✅ Localized capture QA, повний checkpoint, MCP smoke і commit.

---

## Sprint 48 — Animated Avatar Foundation

Ціль: персонаж є модульною 3D-ідентичністю у світі SimCity-подібної міської симуляції, а не керованим героєм або набором незалежних картинок.

Порядок:

1. ✅ Architecture: canonical humanoid rig, environment-driven animation, street-zoom LOD і cinematic intro.
2. ✅ PostgreSQL: one-to-one avatar profile з semantic body/face/hair/outfit codes.
3. ✅ Backend API/tests: 2 body presets, 20 face presets, stock outfit і avatar snapshot/catalog.
4. ✅ Client model/tests: semantic avatar contract без залежності від конкретного style pack.
5. ✅ Повний checkpoint і commit.

Наступний 3D-крок:

1. Виготовити один canonical `.glb` rig із одним outfit та core animation set.
2. Перевірити street-zoom LOD і environment-driven `idle/walk/sit/phone/talk`.

---

## Sprint 49 — Anime Visual Direction

Ціль: перетворити побажання щодо The Legend of Neverland на оригінальний і технічно вимірюваний art contract для нашого `anime` style pack.

Порядок:

1. ✅ Visual bible: персонажі, сучасне місто, матеріали, анімація і межі референсу.
2. ✅ Client palette: світла природна схема sky/cyan/mint/coral/gold.
3. ✅ Asset contract: окрема папка `anime`, naming і безпечний fallback на `core`.
4. ✅ Performance contract: cinematic/street/distance LOD і texture/material budgets.
5. ✅ Повний checkpoint, MCP smoke і commit.

Наступний 3D-крок:

1. Створити один оригінальний canonical anime avatar.
2. Зібрати modern street-corner test у Godot із daylight/evening lighting.
3. Перевірити `idle/walk/sit/phone/talk`, портрет і три рівні LOD.

---

## Checkpoints Де Потрібен Користувач

| Checkpoint | Коли | Що потрібно |
|------------|------|-------------|
| Playtest A | Після Sprint 5 | 5 хв гри: що незрозуміло або ламається |
| Playtest B | Після Sprint 6 | Чи UI відчувається як гра |
| Scope Gate | Перед Sprint 9 | Яку одну gameplay door відкриваємо |

---

## Швидкі Команди

```powershell
.\scripts\pwsh7.ps1 -NoProfile -File .\scripts\check.ps1
.\scripts\play.ps1 -ResetDb -RunCheck
.\scripts\smoke_godot_dashboard.ps1
.\scripts\start_godot_mcp_bridge.ps1
.\scripts\invoke_godot_mcp.ps1 -Tool get_errors -ArgsJson '{"include_warnings":true}'
```

Godot: `C:\Tools\Godot\Godot_v4.3-stable_mono_win64\Godot_v4.3-stable_mono_win64.exe`

PowerShell: `C:\Tools\PowerShell\7.6.2\pwsh.exe`

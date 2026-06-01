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

**MVP hardening перед розширенням гри.**

Мета: core loop `register -> apply -> work -> sleep -> exam -> better job` має бути стабільним, зрозумілим і не ламатися від поганих input/state.

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

1. Status/effects history: останні 3-5 подій після дій гравця.
2. Чіткі loading/busy стани для кнопок під час API-запиту.
3. Error states: backend unavailable, invalid session, no vacancies, insufficient energy.
4. Mobile layout pass: 360x640 і 720x1280 без обрізання тексту.
5. Exam panel polish: варіанти відповідей, disabled submit без відповіді, результат після складання.
6. Playtest через `scripts/play.ps1 -ResetDb -RunCheck`.

DoD:

- Godot MCP `get_errors` = 0.
- Client build проходить.
- Візуальний smoke screenshot після зміни сцени.

---

## Sprint 7 — Balance & 5-Minute Feel

Ціль: MVP loop має бути не тільки правильним, а й відчутно нормальним по темпу.

Порядок:

1. Зафіксувати target loop: скільки змін роботи потрібно до іспиту.
2. Налаштувати зарплату, оренду, exam cost.
3. Додати balance tests: гравець може пройти loop без grind і без infinite money.
4. Перевірити `next_action` після кожного кроку.
5. Оновити README з очікуваним dev playtest сценарієм.

---

## Sprint 8 — Architecture Cleanup

Ціль: підготувати код до наступних систем без великого переписування.

Порядок:

1. Винести повторювані player/job/city queries у repositories або focused service helpers.
2. Переглянути прямі money mutations, де потрібен ledger/debit/credit helper.
3. Додати route-level DTO там, де зараз сирі dict-структури.
4. Зменшити відповідальність `CityDashboardController.cs`, якщо UI стане важким.

Не робити це наперед: тільки після Sprint 5-7 або коли зміна реально спрощує наступний крок.

---

## Sprint 9 — Next Gameplay Door (після стабільного MVP)

Розморожувати тільки одну систему за раз.

Кандидати:

1. Food/basic needs.
2. Simple business ownership.
3. City events/news.
4. Sports as lightweight side progression.

Поки не чіпати:

- Cartels.
- Shadow economy як основний loop.
- Full politics.
- Full insurance/unions.
- Mobile export/release.

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
.\scripts\start_godot_mcp_bridge.ps1
.\scripts\invoke_godot_mcp.ps1 -Tool get_errors -ArgsJson '{"include_warnings":true}'
```

Godot: `C:\Tools\Godot\Godot_v4.3-stable_mono_win64\Godot_v4.3-stable_mono_win64.exe`

PowerShell: `C:\Tools\PowerShell\7.6.2\pwsh.exe`

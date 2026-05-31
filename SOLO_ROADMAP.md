# Solo Roadmap — City Economic Simulator

Проєкт веде **один розробник без команди**. Кожен sprint = одна перевірена ціль.  
Advanced-системи (спорт, картелі, тіньовий сектор) **заморожені** до стабільного MVP.

---

## Як будуємо надійно (головне правило)

> **Повільно, але без оглядки назад.** Краще один маленький шматок, який працює і покритий тестами, ніж п'ять фіч, які потім переробляти.

### Ритм роботи

| Крок | Що робимо |
|------|-----------|
| 1 | Обрати **одну** задачу з поточного sprint |
| 2 | Backend + Alembic (якщо БД) + pytest |
| 3 | Smoke / API loop (`scripts/smoke_mvp.py`) |
| 4 | Godot (якщо стосується UI) + F5 |
| 5 | Оновити roadmap, **commit** — лише коли все зелене |
| 6 | Наступна задача |

### Definition of Done (кожна задача)

- [ ] `pytest` проходить
- [ ] `scripts/check.ps1` проходить (або обґрунтовано `-SkipClient`)
- [ ] Core loop не зламаний (register → work → sleep → exam)
- [ ] Немає «TODO потім» для критичної логіки цієї задачі
- [ ] Зміни закомічені з зрозумілим message

### Зараз НЕ робимо (поки не закриємо борг)

- Нові gameplay-системи (спорт, тінь, картелі)
- Великі рефакторинги «про запас»
- Паралельні sprint-и
- Mobile export до стабільного Godot loop

### Відомий борг (виправити перед новими фічами)

| # | Проблема | План |
|---|----------|------|
| 1 | Подвійна оренда: `sleep` + `game_day_tick` | ✅ Sleep = оренда; tick-day = втома + інфляція |
| 2 | Незакомічені зміни в working tree | Закомітити або відкотити |
| 3 | Checkpoint 2 (5 хв гри в Godot) | Ти граєш, даєш feedback |
| 4 | `sleep` vs `tick-day` не видно в UI | Кнопка «Спати (оренда + відновлення)»; tick — dev-only |

---

## Принципи

1. **Playable > Perfect** — але playable має лишатись playable після кожного commit.
2. **Один sprint — одна перемога** — не розпилюватись.
3. **Тест перед UI** — backend перевіряємо pytest, потім Godot.
4. **Ти потрібен** лише на checkpoint-ах (нижче).

---

## Sprint 1 — Playable Loop ✅

**Ціль:** Godot → register → apply job → work → sleep → exam → краща вакансія.

| Задача | Статус |
|--------|--------|
| Єдиний API envelope `{success, message, data, effects}` | ✅ |
| Ledger + progress до цілі | ✅ |
| MVP routes винесені з monolith | ✅ |
| HTTP-тести повного циклу (pytest) | ✅ |
| Godot `ApiClient` + REST | ✅ |
| Кнопки: apply, work, sleep | ✅ |
| WS лише для city news | ✅ |

### Checkpoint 1 — пропущено (автоперевірка)
- `pytest` — 3/3 passed
- `python scripts/smoke_mvp.py` — повний HTTP-цикл без Godot

---

## Sprint 2 — Feel Like a Game ✅

**Ціль:** гра відчувається, а не як API-demo.

| Задача | Статус |
|--------|--------|
| Прогрес-бар до цілі | ✅ `GoalProgressBar` |
| Екран іспиту (5 питань) | ✅ `ExamPanelController` |
| Кнопка «Скласти іспит» | ✅ |
| Повідомлення `effects` після дій | ✅ `EffectsLabel` |
| Smoke test без Godot | ✅ `scripts/smoke_mvp.py` |
| Dev script | ✅ `scripts/dev.ps1` |

### Checkpoint 2 — **ТИ ПОТРІБЕН** (коли зручно)
- Godot F5 → програти 5 хв → «цікаво / нудно / незрозуміло»

---

## Sprint 3 — Architecture & Balance (майже ✅, **стабілізація**)

**Ціль:** код готовий до росту без переписування.

- Розбити `main.py` (advanced → `routes/frozen.py`) ✅
- Alembic — перша міграція ✅
- Reset script для локальної dev-бази ✅
- FastAPI lifespan замість deprecated startup hook ✅
- `game_day_tick` + формули з `economic_formulas.md` (спрощено) ✅
- Баланс-тест: 30 ігрових днів без infinite money ✅
- Dev endpoint `POST /api/city/tick-day` + smoke coverage ✅
- Idempotency для `work/sleep/exam` ✅
- **→ Наступний крок:** узгодити модель дня (sleep vs tick), не додавати нове

### Checkpoint 3 — **ТИ ПОТРІБЕН**
- Програти 5 хв після auth/idempotency
- Рішення: чи розморожувати спорт/тіньовий сектор (**рекомендація: ні, поки не стабільно**)

---

## Sprint 4 — Polish (поточний, **повільно**)

Порядок — **строго по одному пункту**:

1. ✅ Узгодити «день/ніч» (оренда, енергія) — backend + тест + UI
2. ✅ Godot UI polish (feedback, disabled buttons, помилки сесії)
2b. ✅ Підказка «Наступний крок» (backend `next_action` + UI)
2c. ✅ Backend-driven action availability для кнопок Godot
3. ✅ Playtest launch path: `.\scripts\play.ps1 -ResetDb -RunCheck`
4. ⬜ Checkpoint 2 — твій feedback «цікаво / нудно»
5. ⬜ Mobile export (останнім)

Вже зроблено:
- Auth (простий token) ✅
- Idempotency для work/sleep/exam ✅
- CI: backend pytest + Godot C# build on push ✅

---

## Заморожено (не чіпати до Sprint 3+)

```
POST /api/shadow/*
POST /api/sports/*
POST /api/advanced/*
POST /api/police/*
```

Код залишається, але не розвивається.

---

## Швидкий старт (dev)

```powershell
docker compose up -d postgres
copy .env.example .env
pip install -r backend/requirements-dev.txt
python -m uvicorn backend.main:app --reload
pytest
```

Godot 4.3 .NET → відкрити `client/` → F5.

---

## Коли писати мені

| Ситуація | Дія |
|----------|-----|
| Backend не стартує | Скинь помилку з термінала |
| Godot не підключається | Перевір backend + CORS |
| Checkpoint sprint | Програй і дай feedback |
| Нова велика фіча | Спочатку обговоримо scope |

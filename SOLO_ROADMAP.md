# Solo Roadmap — City Economic Simulator

Проєкт веде **один розробник без команди**. Кожен sprint = одна перевірена ціль.  
Advanced-системи (спорт, картелі, тіньовий сектор) **заморожені** до playable MVP.

---

## Принципи

1. **Playable > Perfect** — спочатку можна програти 5 хвилин, потім архітектура.
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

## Sprint 3 — Architecture & Balance (поточний)

**Ціль:** код готовий до росту без переписування.

- Розбити `main.py` (advanced → `routes/frozen.py`)
- Alembic — перша міграція ✅
- Reset script для локальної dev-бази ✅
- FastAPI lifespan замість deprecated startup hook ✅
- `game_day_tick` + формули з `economic_formulas.md` (спрощено) ✅
- Баланс-тест: 30 ігрових днів без infinite money ✅
- Dev endpoint `POST /api/city/tick-day` + smoke coverage ✅
- Idempotency для `work/sleep/exam` ✅

### Checkpoint 3 — **ТИ ПОТРІБЕН**
- Рішення: чи розморожувати спорт/тіньовий сектор

---

## Sprint 4 — Polish & Deploy Prep

- Auth (простий token) ✅
- Idempotency для work/sleep/exam ✅
- Godot UI polish (mobile portrait)
- CI: pytest on push

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

Godot 4.2 .NET → відкрити `client/` → F5.

---

## Коли писати мені

| Ситуація | Дія |
|----------|-----|
| Backend не стартує | Скинь помилку з термінала |
| Godot не підключається | Перевір backend + CORS |
| Checkpoint sprint | Програй і дай feedback |
| Нова велика фіча | Спочатку обговоримо scope |

# Бізнес-логіка економічних процесів: Робота, Оренда, Оподаткування та Інфляція
# Файл: backend/app/services/economy.py

from decimal import Decimal
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.models import Player, City, Job, Hostel, TransactionModelLog, Business
from backend.app.services.ids import to_uuid
from backend.app.services.job_queries import get_active_job
from backend.app.services.ledger import credit, debit, log_transaction
from backend.app.services.money import money
from backend.app.services.needs import DAY_HUNGER_INCREASE, SLEEP_HUNGER_INCREASE, WORK_HUNGER_INCREASE, increase_hunger


def _active_money_supply(db: Session, city_id) -> Decimal:
    players_balance = db.query(func.sum(Player.balance)).filter(Player.city_id == city_id).scalar() or 0
    businesses_balance = db.query(func.sum(Business.cash_balance)).filter(
        Business.city_id == city_id,
        Business.owner_player_id.isnot(None),
    ).scalar() or 0
    return money(players_balance) + money(businesses_balance)


def process_shift_work(db: Session, player_id: str) -> dict:
    """Обробка робочої зміни гравця (Виснаження енергії, виплата ЗП, сплата податку в Скарбницю)"""
    player_uuid = to_uuid(player_id)
    player = db.query(Player).filter(Player.id == player_uuid).first()
    if not player:
        return {"success": False, "message": "Гравця не знайдено"}

    job = get_active_job(db, player_uuid)
    if not job:
        return {"success": False, "message": "Ви не працевлаштовані. Знайдіть роботу в Центрі Зайнятості."}

    # Перевірка на активний страйк профспілки
    from backend.app.models import LaborUnion
    union = db.query(LaborUnion).filter(LaborUnion.business_id == job.business_id).first()
    if union and union.strike_active:
        return {"success": False, "message": f"❌ СТРАЙК! Профспілка підприємства '{job.business.name}' оголосила страйк. Робочі зміни заблоковано."}

    # Перевірка ліміту енергії
    if player.energy < job.energy_cost_per_shift:
        return {"success": False, "message": f"Недостатньо енергії! Необхідно: {job.energy_cost_per_shift}, у вас: {player.energy}. Спочатку відпочиньте."}

    city = db.query(City).filter(City.id == player.city_id).first()
    business = db.query(Business).filter(Business.id == job.business_id).first()

    # Розрахунок ЗП
    hours = 8
    gross_salary = money(job.salary_per_hour) * hours
    
    # Розрахунок податку
    income_tax_rate = money(city.tax_rate_income) / Decimal("100.00")
    tax_amount = gross_salary * income_tax_rate
    net_salary = gross_salary - tax_amount

    # Виконання транзакції
    player.energy -= job.energy_cost_per_shift
    increase_hunger(player, WORK_HUNGER_INCREASE)
    credit(db, player, "balance", net_salary)
    
    # Зміна балансів казначейства та бізнесу
    credit(db, city, "treasury_balance", tax_amount)
    
    # Зарплата виплачується з балансу бізнесу (якщо це приватний) або казначейства (державний)
    if business.owner_player_id is None:  # Комунальне/державне підприємство
        debit(db, city, "treasury_balance", gross_salary)
    else:
        debit(db, business, "cash_balance", gross_salary)

    # Логування ЗП
    salary_sender_id = city.id if business.owner_player_id is None else business.id
    salary_sender_type = "treasury" if business.owner_player_id is None else "business"
    log_transaction(
        db, city.id, 
        sender_id=salary_sender_id, sender_type=salary_sender_type,
        receiver_id=player.id, receiver_type="player",
        amount=float(net_salary), tax=float(tax_amount),
        purpose="salary"
    )

    db.commit()

    return {
        "success": True,
        "message": f"Зміну успішно відпрацьовано! Отримано {net_salary:.2f} ₴ (після податку {city.tax_rate_income}%).",
        "player": {
            "balance": float(player.balance),
            "energy": player.energy,
            "hunger": player.hunger,
        },
        "city": {
            "treasury_balance": float(city.treasury_balance)
        }
    }

def process_rent_payment(db: Session, player_id: str) -> dict:
    """Нічний сон гравця: одноразова оплата оренди та відновлення енергії/настрою."""
    player_uuid = to_uuid(player_id)
    player = db.query(Player).filter(Player.id == player_uuid).first()
    if not player:
        return {"success": False, "message": "Гравця не знайдено"}

    hostel = db.query(Hostel).filter(Hostel.tenant_player_id == player_uuid).first()
    if not hostel:
        return {"success": False, "message": "У вас немає орендованого житла. Ви спите на вулиці."}

    city = db.query(City).filter(City.id == player.city_id).first()
    business = db.query(Business).filter(Business.id == hostel.business_id).first()

    rent_price = money(hostel.rent_price_per_day)

    # Перевірка наявності коштів
    if money(player.balance) >= rent_price:
        debit(db, player, "balance", rent_price)
        player.energy = min(100, player.energy + (hostel.energy_regen_per_hour * 8)) # 8 годин сну
        player.mood = min(100, player.mood + 15)
        increase_hunger(player, SLEEP_HUNGER_INCREASE)
        
        # Гроші за оренду йдуть власнику хостелу (приватний бізнес або Скарбниця міста)
        if business.owner_player_id is None:
            credit(db, city, "treasury_balance", rent_price)
        else:
            credit(db, business, "cash_balance", rent_price)

        log_transaction(
            db, city.id,
            sender_id=player.id, sender_type="player",
            receiver_id=city.id if business.owner_player_id is None else business.id,
            receiver_type="treasury" if business.owner_player_id is None else "business",
            amount=float(rent_price), tax=0.0,
            purpose="rent"
        )
        message = f"Сплачено {rent_price:.2f} ₴ за оренду хостелу. Ви чудово виспались!"
    else:
        # Безкоштовний сон на вулиці (погане відновлення)
        player.energy = min(100, player.energy + 20)
        player.mood = max(10, player.mood - 20)
        increase_hunger(player, SLEEP_HUNGER_INCREASE)
        message = "Недостатньо коштів на оренду! Ви спали на лавці в парку. Енергія майже не відновилась."

    db.commit()
    return {
        "success": True,
        "message": message,
        "player": {
            "balance": float(player.balance),
            "energy": player.energy,
            "mood": player.mood,
            "hunger": player.hunger,
        }
    }

def update_inflation_rate(db: Session, city_id: str) -> float:
    """Автоматичний прорахунок активної грошової маси та інфляції"""
    city_uuid = to_uuid(city_id)
    city = db.query(City).filter(City.id == city_uuid).first()
    if not city:
        return 0.0

    # Грошова маса у гравців
    players_balance = db.query(func.sum(Player.balance)).filter(Player.city_id == city_uuid).scalar() or 0.0
    # Грошова маса в приватному бізнесі
    businesses_balance = db.query(func.sum(Business.cash_balance)).filter(
        Business.city_id == city_uuid, 
        Business.owner_player_id.isnot(None)
    ).scalar() or 0.0

    active_money = float(players_balance) + float(businesses_balance)
    
    # Базове цільове зростання (наприклад, 500 ₴ на кожного гравця)
    num_players = db.query(func.count(Player.id)).filter(Player.city_id == city_uuid).scalar() or 1
    target_circulation = num_players * 600.00
    
    if active_money > target_circulation:
        growth = (active_money - target_circulation) / target_circulation
        city.inflation_rate = money(round(growth * 100, 2))
    else:
        city.inflation_rate = money("0.00")

    db.commit()
    return float(city.inflation_rate)


def game_day_tick(db: Session, city_id: str) -> dict:
    """Dev-тick міста: пасивна втома, настрій та інфляція. Оренда — лише через sleep."""
    city_uuid = to_uuid(city_id)
    city = db.query(City).filter(City.id == city_uuid).first()
    if not city:
        return {"success": False, "message": "Місто не знайдено"}

    active_before = _active_money_supply(db, city_uuid)
    players_updated = 0
    homeless_players = 0
    hungry_players = 0

    players = db.query(Player).filter(Player.city_id == city_uuid).all()
    for player in players:
        players_updated += 1
        player.energy = max(0, player.energy - 5)
        player.mood = max(10, player.mood - 2)
        increase_hunger(player, DAY_HUNGER_INCREASE)
        if player.hunger >= 90:
            hungry_players += 1
            player.mood = max(10, player.mood - 5)

        hostel = db.query(Hostel).filter(Hostel.tenant_player_id == player.id).first()
        if not hostel:
            homeless_players += 1
            player.mood = max(10, player.mood - 8)

    active_after = _active_money_supply(db, city_uuid)
    player_count = max(1, len(players))
    target_circulation = money(player_count * 600)
    if active_after > target_circulation:
        growth = (active_after - target_circulation) / target_circulation
        city.inflation_rate = money(round(growth * 100, 2))
    else:
        city.inflation_rate = money("0.00")

    db.commit()

    return {
        "success": True,
        "message": "Настав новий день. Оренду сплачуйте кнопкою «Спати».",
        "city": {
            "id": str(city.id),
            "inflation_rate": float(city.inflation_rate),
            "treasury_balance": float(city.treasury_balance),
        },
        "stats": {
            "players_updated": players_updated,
            "rent_collected": 0.0,
            "homeless_players": homeless_players,
            "hungry_players": hungry_players,
            "active_money_before": float(active_before),
            "active_money_after": float(active_after),
        },
    }

# Бізнес-логіка спортивної екосистеми: Тренування, Трансфери та Симуляція Матчів Ліги
# Файл: backend/app/services/sports.py

import random
from decimal import Decimal

from sqlalchemy.orm import Session, joinedload

from backend.app.models import Player, SportsClub, PlayerAthleteContract, City
from backend.app.schemas.service_results import (
    SportsContractServiceResult,
    SportsLeagueMatchServiceResult,
    SportsLeagueMessageServiceResult,
    SportsTrainServiceResult,
)
from backend.app.services.ledger import credit, debit, log_transaction
from backend.app.services.ids import to_uuid


def money(value) -> Decimal:
    return Decimal(str(value))


GYM_COST = money("40.00")
GYM_ENERGY_COST = 40


def train_at_gym(db: Session, player_id: str, stat_to_train: str) -> dict:
    """Тренування у Спортзалі (Витрачає енергію та гроші, прокачує силу/витривалість)"""
    player_uuid = to_uuid(player_id)
    player = db.query(Player).filter(Player.id == player_uuid).first()
    if not player:
        return {"success": False, "message": "Гравця не знайдено"}

    if stat_to_train not in ("strength", "stamina"):
        return {"success": False, "message": "Невідомий тип тренування"}

    if money(player.balance) < GYM_COST:
        return {
            "success": False,
            "message": f"Недостатньо грошей на абонемент! Потрібно: {GYM_COST} ₴",
        }
    if player.energy < GYM_ENERGY_COST:
        return {
            "success": False,
            "message": f"Недостатньо енергії для тренування! Потрібно: {GYM_ENERGY_COST}%",
        }

    # Знаходження контракту гравця або створення стартового
    contract = (
        db.query(PlayerAthleteContract)
        .filter(PlayerAthleteContract.player_id == player_uuid)
        .first()
    )
    if not contract:
        # Якщо контракту немає, створюємо аматорський статус (без клубу)
        # Для простоти MVP, гравець повинен спершу підписати контракт або мати запис характеристик
        return {
            "success": False,
            "message": "Спочатку підпишіть контракт у Центрі Зайнятості чи Спортивній Асоціації.",
        }

    # Списання ресурсів
    debit(db, player, "balance", GYM_COST)
    player.energy -= GYM_ENERGY_COST

    # Гроші за спортзал йдуть у міську скарбницю (або власнику спортзалу)
    city = db.query(City).filter(City.id == player.city_id).first()
    credit(db, city, "treasury_balance", GYM_COST)

    # Прокачування статів
    gain = random.randint(2, 5)
    if stat_to_train == "strength":
        contract.strength_stat += gain
        message = f"🏋️ Ви чудово потиснули штангу! Сила зросла на +{gain} (Поточна Сила: {contract.strength_stat})."
    else:
        contract.stamina_stat += gain
        message = f"🏃 Ви відбігали 10 км на доріжці! Витривалість зросла на +{gain} (Поточна Витривалість: {contract.stamina_stat})."

    log_transaction(
        db,
        city.id,
        sender_id=player.id,
        sender_type="player",
        receiver_id=city.id,
        receiver_type="treasury",
        amount=float(GYM_COST),
        tax=0.0,
        purpose="gym_training",
    )

    db.commit()
    return SportsTrainServiceResult(
        success=True,
        message=message,
        player={"balance": float(player.balance), "energy": player.energy},
        stats={"strength": contract.strength_stat, "stamina": contract.stamina_stat},
    ).model_dump()


def sign_athlete_contract(
    db: Session, player_id: str, club_id: str, salary: float
) -> dict:
    """Підписання контракту спортсмена з клубом"""
    player_uuid = to_uuid(player_id)
    club_uuid = to_uuid(club_id)
    player = db.query(Player).filter(Player.id == player_uuid).first()
    club = db.query(SportsClub).filter(SportsClub.id == club_uuid).first()

    if not player or not club:
        return {"success": False, "message": "Гравця чи клуб не знайдено"}

    # Перевірка наявності чинного контракту
    existing = (
        db.query(PlayerAthleteContract)
        .filter(PlayerAthleteContract.player_id == player_uuid)
        .first()
    )
    if existing:
        return {
            "success": False,
            "message": "У вас вже є чинний спортивний контракт! Розірвіть старий контракт спочатку.",
        }

    # Підписання
    contract = PlayerAthleteContract(
        player_id=player.id,
        club_id=club.id,
        salary_per_match=money(salary),
        role="player",
        contract_status="active",
        strength_stat=10,
        stamina_stat=10,
    )
    db.add(contract)
    db.commit()

    return SportsContractServiceResult(
        success=True,
        message=f"Вітаємо! Ви стали професійним атлетом клубу '{club.name}' із зарплатою {salary:.2f} ₴ за матч!",
    ).model_dump()


def simulate_league_matches(db: Session, city_id: str) -> list:
    """Симуляція матчів ліги міста (ШІ-симуляція на основі сили команд)"""
    city_uuid = to_uuid(city_id)
    clubs = db.query(SportsClub).filter(SportsClub.city_id == city_uuid).all()
    if len(clubs) < 2:
        return [
            SportsLeagueMessageServiceResult(
                message="Недостатньо клубів для проведення матчів ліги.",
            ).model_dump()
        ]

    results = []

    # Проста кругова система: кожен грає з кожним (парами)
    for i in range(len(clubs)):
        for j in range(i + 1, len(clubs)):
            club_a = clubs[i]
            club_b = clubs[j]

            # Розрахунок сили команди А
            # Сила = Базова ефективність клубу + сума статсів усіх залучених реальних гравців
            contracts_a = (
                db.query(PlayerAthleteContract)
                .filter(
                    PlayerAthleteContract.club_id == club_a.id,
                    PlayerAthleteContract.contract_status == "active",
                )
                .all()
            )
            strength_a = 50 + sum(c.strength_stat + c.stamina_stat for c in contracts_a)

            # Розрахунок сили команди Б
            contracts_b = (
                db.query(PlayerAthleteContract)
                .filter(
                    PlayerAthleteContract.club_id == club_b.id,
                    PlayerAthleteContract.contract_status == "active",
                )
                .all()
            )
            strength_b = 50 + sum(c.strength_stat + c.stamina_stat for c in contracts_b)

            # Симуляція матчу на основі шансів
            total_strength = strength_a + strength_b
            roll = random.randint(1, total_strength)

            if roll <= strength_a:
                # Перемога клубу А
                winner = club_a
                score_w = random.randint(1, 4)
                score_l = random.randint(0, score_w - 1)
            else:
                # Перемога клубу Б
                winner = club_b
                score_w = random.randint(1, 4)
                score_l = random.randint(0, score_w - 1)

            # Оновлення результатів ліги
            winner.league_points += 3
            results.append(
                SportsLeagueMatchServiceResult(
                    match=f"{club_a.name} VS {club_b.name}",
                    result=f"{winner.name} виграв з рахунком {score_w}:{score_l}",
                    winner_id=str(winner.id),
                ).model_dump()
            )

            # ЕКОНОМІКА МАТЧУ: Збори з квитків
            # Дохід = Місткість стадіону * Ціна квитка * (0.4 - 1.0 заповнюваність залежно від рейтингу)
            fill_rate = min(1.0, 0.4 + (winner.league_points * 0.05))
            tickets_sold = int(winner.stadium_capacity * fill_rate)
            revenue = money(tickets_sold) * money(winner.ticket_price)

            # Нарахування прибутку на рахунок клубу
            credit(db, winner, "cash_balance", revenue)
            log_transaction(
                db,
                city_id,
                sender_id=city_uuid,
                sender_type="system",
                receiver_id=winner.id,
                receiver_type="business",
                amount=float(revenue),
                tax=0.0,
                purpose="ticket_revenue",
            )

            # ВИПЛАТА ЗАРПЛАТ АТЛЕТАМ:
            # Зарплати виплачуються з бюджету клубу
            winner_contracts = (
                db.query(PlayerAthleteContract)
                .options(joinedload(PlayerAthleteContract.player))
                .filter(PlayerAthleteContract.club_id == winner.id)
                .all()
            )
            for c in winner_contracts:
                p = c.player
                salary = money(c.salary_per_match)
                credit(db, p, "balance", salary)
                debit(db, winner, "cash_balance", salary)

                log_transaction(
                    db,
                    city_id,
                    sender_id=winner.id,
                    sender_type="business",
                    receiver_id=p.id,
                    receiver_type="player",
                    amount=float(salary),
                    tax=0.0,
                    purpose="athlete_match_salary",
                )

    db.commit()
    return results

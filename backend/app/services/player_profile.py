from decimal import Decimal

from sqlalchemy.orm import Session

from backend.app.models import Hostel, Job, Player
from backend.app.schemas.mvp import PlayerActionsData, PlayerSnapshotData
from backend.app.services.business_market import cheapest_business_price, get_owned_businesses
from backend.app.services.education import load_manager_exam
from backend.app.services.ids import to_uuid
from backend.app.services.job_queries import education_rank, get_active_job, has_eligible_vacancy
from backend.app.services.money import money
from backend.app.services.needs import MEAL_COST
from backend.app.services.onboarding import build_onboarding_snapshot, is_onboarding_complete
from backend.app.services.player_progress import build_goal_effects
from backend.app.services.sports import GYM_COST, GYM_ENERGY_COST


def build_player_actions(db: Session, player: Player, job: Job | None, hostel: Hostel | None) -> dict:
    if not is_onboarding_complete(db, player):
        return PlayerActionsData(
            can_apply_job=False,
            can_work=False,
            can_sleep=False,
            can_eat=False,
            can_buy_business=False,
            can_collect_dividend=False,
            can_join_sports=False,
            can_train_sports=False,
            can_take_exam=False,
        ).model_dump()

    exam = load_manager_exam()
    exam_cost = money(exam.get("cost_to_take", 100)) if exam else Decimal("100.00")

    return PlayerActionsData(
        can_apply_job=has_eligible_vacancy(db, player.education_level),
        can_work=bool(job and player.energy >= job.energy_cost_per_shift),
        can_sleep=hostel is not None,
        can_eat=(player.hunger or 0) > 0 and money(player.balance) >= MEAL_COST,
        can_buy_business=(cheapest_business_price(db) or Decimal("999999999.00")) <= money(player.balance),
        can_collect_dividend=any(money(b.cash_balance) >= Decimal("250.00") for b in get_owned_businesses(db, player.id)),
        can_join_sports=player.athlete_contract is None,
        can_train_sports=bool(player.athlete_contract and money(player.balance) >= GYM_COST and player.energy >= GYM_ENERGY_COST),
        can_take_exam=player.education_level == "High School" and money(player.balance) >= exam_cost,
    ).model_dump()


def build_player_snapshot(db: Session, player: Player) -> dict:
    job = get_active_job(db, player.id)
    hostel = db.query(Hostel).filter(Hostel.tenant_player_id == player.id).first()
    actions = build_player_actions(db, player, job, hostel)
    owned_businesses = get_owned_businesses(db, player.id)
    athlete_contract = player.athlete_contract

    snapshot = PlayerSnapshotData(
        id=str(player.id),
        username=player.username,
        balance=float(player.balance),
        energy=player.energy,
        mood=player.mood,
        hunger=player.hunger,
        education_level=player.education_level,
        diploma_verified=player.diploma_verified,
        job=job.title if job else "Безробітний",
        job_id=str(job.id) if job else None,
        hostel=f"Кімната №{hostel.room_number} (Хостел)" if hostel else "На вулиці",
        owned_businesses=[
            {
                "id": str(b.id),
                "name": b.name,
                "type": b.type,
                "cash_balance": float(b.cash_balance),
            }
            for b in owned_businesses
        ],
        sports_contract={
            "club": athlete_contract.club.name,
            "strength": athlete_contract.strength_stat,
            "stamina": athlete_contract.stamina_stat,
            "salary_per_match": float(athlete_contract.salary_per_match),
        }
        if athlete_contract
        else None,
        onboarding=build_onboarding_snapshot(db, player),
        actions=actions,
        goal_effects=build_goal_effects(db, player),
    )
    return snapshot.model_dump()


def get_player_snapshot(db: Session, player_id: str) -> dict | None:
    player = db.query(Player).filter(Player.id == to_uuid(player_id)).first()
    if not player:
        return None
    return build_player_snapshot(db, player)

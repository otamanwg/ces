from decimal import Decimal

from sqlalchemy.orm import Session

from backend.app.models import Job, Player
from backend.app.schemas.response import GameEffect
from backend.app.services.education import load_manager_exam
from backend.app.services.money import money


def build_goal_effects(db: Session, player: Player) -> list[dict]:
    effects: list[dict] = []
    balance = money(player.balance)

    if player.education_level == "High School":
        exam = load_manager_exam()
        exam_cost = money(exam.get("cost_to_take", 100)) if exam else money("100.00")
        pct = int(min(Decimal("100"), (balance / exam_cost) * Decimal("100")))
        effects.append(
            GameEffect(
                key="goal_manager_cert",
                label="Сертифікат менеджера",
                value=f"{pct}%",
                delta=f"Потрібно {exam_cost:.0f} ₴ на іспит",
            ).model_dump()
        )
    elif player.education_level == "College":
        manager_job = (
            db.query(Job)
            .filter(Job.min_education == "College", Job.filled_by_player_id.is_(None))
            .first()
        )
        if manager_job:
            effects.append(
                GameEffect(
                    key="goal_better_job",
                    label="Краща посада",
                    value=manager_job.title,
                    delta="Вакансія доступна",
                ).model_dump()
            )

    effects.append(
        GameEffect(
            key="stability_energy",
            label="Енергія",
            value=f"{player.energy}/100",
            delta=None,
        ).model_dump()
    )
    effects.append(
        GameEffect(
            key="stability_mood",
            label="Настрій",
            value=f"{player.mood}/100",
            delta=None,
        ).model_dump()
    )

    return effects

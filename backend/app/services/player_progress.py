from decimal import Decimal

from sqlalchemy.orm import Session

from backend.app.models import Player
from backend.app.schemas.response import GameEffect
from backend.app.services.education import load_manager_exam
from backend.app.services.job_queries import get_active_job, get_first_vacant_job_by_min_education
from backend.app.services.money import money
from backend.app.services.needs import HUNGER_WARNING_THRESHOLD, MEAL_COST


def build_next_action_hint(db: Session, player: Player) -> dict:
    """Підказка наступної дії для MVP loop (work → sleep → exam → краща робота)."""
    job = get_active_job(db, player.id)

    if not job:
        if player.education_level == "College":
            college_job = get_first_vacant_job_by_min_education(db, "College")
            if college_job:
                return GameEffect(
                    key="next_action",
                    label="Наступний крок",
                    value="Влаштуйтесь на кращу посаду",
                    delta=college_job.title,
                ).model_dump()
        return GameEffect(
            key="next_action",
            label="Наступний крок",
            value="Влаштуйтесь на роботу",
            delta=None,
        ).model_dump()

    if player.education_level == "College" and job.min_education == "High School":
        college_job = get_first_vacant_job_by_min_education(db, "College")
        if college_job:
            return GameEffect(
                key="next_action",
                label="Наступний крок",
                value="Влаштуйтесь на кращу посаду",
                delta=college_job.title,
            ).model_dump()

    if player.energy < job.energy_cost_per_shift:
        return GameEffect(
            key="next_action",
            label="Наступний крок",
            value="Спати (оренда + відновлення)",
            delta=f"Потрібно {job.energy_cost_per_shift} енергії, у вас {player.energy}",
        ).model_dump()

    if (player.hunger or 0) >= HUNGER_WARNING_THRESHOLD:
        return GameEffect(
            key="next_action",
            label="Наступний крок",
            value="Поїжте",
            delta=f"Голод {player.hunger}/100, обід {MEAL_COST:.0f} ₴",
        ).model_dump()

    if player.education_level == "High School":
        exam = load_manager_exam()
        exam_cost = money(exam.get("cost_to_take", 100)) if exam else money("100.00")
        if money(player.balance) >= exam_cost:
            return GameEffect(
                key="next_action",
                label="Наступний крок",
                value="Складіть іспит у коледж",
                delta=f"Достатньо коштів ({exam_cost:.0f} ₴)",
            ).model_dump()

    return GameEffect(
        key="next_action",
        label="Наступний крок",
        value="Відпрацюйте зміну",
        delta=job.title,
    ).model_dump()


def build_goal_effects(db: Session, player: Player) -> list[dict]:
    effects: list[dict] = [build_next_action_hint(db, player)]
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
        manager_job = get_first_vacant_job_by_min_education(db, "College")
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
    effects.append(
        GameEffect(
            key="stability_hunger",
            label="Голод",
            value=f"{player.hunger}/100",
            delta=None,
        ).model_dump()
    )

    return effects

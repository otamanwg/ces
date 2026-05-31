from typing import Dict

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.database import get_db
from backend.app.models import City, Hostel, Job, Player
from backend.app.schemas.response import api_error, api_success
from backend.app.services.economy import game_day_tick, process_rent_payment, process_shift_work, update_inflation_rate
from backend.app.services.education import load_manager_exam, process_exam_submission
from backend.app.services.ids import to_uuid
from backend.app.services.idempotency import get_idempotent_response, save_idempotent_response
from backend.app.services.player_profile import build_player_snapshot, get_player_snapshot
from backend.app.services.player_progress import build_goal_effects

router = APIRouter(prefix="/api", tags=["mvp"])


class PlayerRegister(BaseModel):
    username: str


class JobApply(BaseModel):
    player_id: str
    job_id: str


class ExamAnswers(BaseModel):
    player_id: str
    answers: Dict[str, int]


@router.get("/city/status")
def get_city_status(db: Session = Depends(get_db)):
    city = db.query(City).first()
    if not city:
        raise HTTPException(status_code=404, detail="Місто не знайдене")

    update_inflation_rate(db, city.id)
    data = {
        "id": str(city.id),
        "name": city.name,
        "treasury_balance": float(city.treasury_balance),
        "tax_rate_income": float(city.tax_rate_income),
        "tax_rate_property": float(city.tax_rate_property),
        "inflation_rate": float(city.inflation_rate),
    }
    return api_success("Статус міста оновлено.", data)


@router.post("/city/tick-day")
def run_city_day_tick(db: Session = Depends(get_db)):
    if not settings.debug:
        raise HTTPException(status_code=403, detail="Day tick endpoint is available only in debug mode.")

    city = db.query(City).first()
    if not city:
        return api_error("Місто не знайдене.")

    res = game_day_tick(db, str(city.id))
    if not res["success"]:
        return api_error(res["message"])
    return api_success(res["message"], {"city": res["city"], "stats": res["stats"]})


@router.post("/player/register")
def register_player(data: PlayerRegister, db: Session = Depends(get_db)):
    username = data.username.strip()
    if not username:
        return api_error("Ім'я не може бути порожнім.")

    existing = db.query(Player).filter(Player.username == username).first()
    if existing:
        return api_error("Громадянин з таким ім'ям вже зареєстрований.")

    city = db.query(City).first()
    if not city:
        return api_error("Місто ще не ініціалізоване.")

    player = Player(
        city_id=city.id,
        username=username,
        balance=500.00,
        energy=100,
        mood=100,
        education_level="High School",
    )
    db.add(player)
    db.commit()
    db.refresh(player)

    free_room = db.query(Hostel).filter(Hostel.tenant_player_id.is_(None)).first()
    if free_room:
        free_room.tenant_player_id = player.id
        db.commit()

    snapshot = build_player_snapshot(db, player)
    effects = build_goal_effects(db, player)
    hostel_msg = snapshot["hostel"]
    return api_success(
        f"Ласкаво просимо, {username}! Вас поселено: {hostel_msg}.",
        snapshot,
        effects,
    )


@router.get("/player/{player_id}")
def get_player_status(player_id: str, db: Session = Depends(get_db)):
    snapshot = get_player_snapshot(db, player_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Гравця не знайдено")
    return api_success("Статус гравця.", snapshot, snapshot.get("goal_effects", []))


@router.get("/jobs/vacancies")
def get_vacancies(db: Session = Depends(get_db)):
    vacancies = db.query(Job).filter(Job.filled_by_player_id.is_(None)).all()
    data = {
        "vacancies": [
            {
                "id": str(j.id),
                "business_name": j.business.name,
                "title": j.title,
                "salary_per_hour": float(j.salary_per_hour),
                "min_education": j.min_education,
                "energy_cost": j.energy_cost_per_shift,
            }
            for j in vacancies
        ]
    }
    return api_success("Доступні вакансії.", data)


@router.post("/jobs/apply")
def apply_for_job(data: JobApply, db: Session = Depends(get_db)):
    player = db.query(Player).filter(Player.id == to_uuid(data.player_id)).first()
    job = db.query(Job).filter(Job.id == to_uuid(data.job_id)).first()

    if not player or not job:
        return api_error("Гравця або вакансію не знайдено.")

    if job.filled_by_player_id is not None:
        return api_error("Ця вакансія вже зайнята.")

    education_levels = {"High School": 1, "College": 2, "University": 3}
    player_rank = education_levels.get(player.education_level, 1)
    required_rank = education_levels.get(job.min_education, 1)

    if player_rank < required_rank:
        return api_error(
            f"Недостатня освіта! Потрібно '{job.min_education}', у вас '{player.education_level}'.",
            {"required_education": job.min_education},
        )

    old_job = db.query(Job).filter(Job.filled_by_player_id == player.id).first()
    if old_job:
        old_job.filled_by_player_id = None
        db.flush()

    job.filled_by_player_id = player.id
    db.commit()

    snapshot = build_player_snapshot(db, player)
    return api_success(
        f"Вас працевлаштовано на '{job.title}'.",
        snapshot,
        build_goal_effects(db, player),
    )


@router.post("/jobs/work/{player_id}")
def do_work_shift(
    player_id: str,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
):
    cached = get_idempotent_response(db, "work_shift", idempotency_key, player_id)
    if cached:
        return cached

    res = process_shift_work(db, player_id)
    if not res["success"]:
        return api_error(res["message"])

    player = db.query(Player).filter(Player.id == to_uuid(player_id)).first()
    snapshot = build_player_snapshot(db, player)
    effects = build_goal_effects(db, player)
    data = {**snapshot, "city": res.get("city", {})}
    response = api_success(res["message"], data, effects)
    return save_idempotent_response(db, "work_shift", idempotency_key, player_id, response)


@router.post("/hostels/sleep/{player_id}")
def sleep_in_hostel(
    player_id: str,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
):
    cached = get_idempotent_response(db, "sleep", idempotency_key, player_id)
    if cached:
        return cached

    res = process_rent_payment(db, player_id)
    if not res["success"]:
        return api_error(res["message"])

    player = db.query(Player).filter(Player.id == to_uuid(player_id)).first()
    snapshot = build_player_snapshot(db, player)
    response = api_success(res["message"], snapshot, build_goal_effects(db, player))
    return save_idempotent_response(db, "sleep", idempotency_key, player_id, response)


@router.get("/education/exam/info")
def get_exam_details():
    exam = load_manager_exam()
    if not exam:
        raise HTTPException(status_code=404, detail="Файл квізу не знайдено на сервері")

    clean_exam = {
        "exam_id": exam["exam_id"],
        "title": exam["title"],
        "cost_to_take": exam["cost_to_take"],
        "passing_score": exam["passing_score"],
        "time_limit_seconds": exam["time_limit_seconds"],
        "description": exam["description"],
        "questions": [
            {"id": q["id"], "text": q["text"], "options": q["options"]}
            for q in exam["questions"]
        ],
    }
    return api_success("Інформація про іспит.", clean_exam)


@router.post("/education/exam/submit")
def submit_exam(
    data: ExamAnswers,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
):
    cached = get_idempotent_response(db, "exam_submit", idempotency_key, data.player_id)
    if cached:
        return cached

    res = process_exam_submission(db, data.player_id, data.answers)
    if not res["success"]:
        return api_error(res["message"])

    player = db.query(Player).filter(Player.id == to_uuid(data.player_id)).first()
    snapshot = build_player_snapshot(db, player)
    data_out = {
        **snapshot,
        "passed": res.get("passed"),
        "score": res.get("score"),
        "details": res.get("details", []),
    }
    response = api_success(res["message"], data_out, build_goal_effects(db, player))
    return save_idempotent_response(db, "exam_submit", idempotency_key, data.player_id, response)

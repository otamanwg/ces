from typing import Dict

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.api.responses import build_player_action_response, save_player_action_response
from backend.app.database import get_db
from backend.app.models import Building, BuildingApplication, City, Hostel, LandParcel, Player, SportsClub
from backend.app.schemas.mvp import (
    BuildingApplicationData,
    BuildingActivationActionData,
    BuildingItem,
    BusinessMarketData,
    BusinessMarketItem,
    BusinessBuyActionData,
    BusinessDividendActionData,
    CityDistrictItem,
    CityStatusData,
    DayTickData,
    ExamSubmitActionData,
    ExamInfoData,
    ExamQuestionData,
    LandParcelItem,
    LandParcelsData,
    LandPurchaseActionData,
    MayorPolicyIssueData,
    SportsClubItem,
    SportsClubsData,
    SportsTrainActionData,
    VacanciesData,
    VacancyItem,
    WorkActionData,
)
from backend.app.schemas.response import api_error, api_success
from backend.app.services.auth import get_authorized_player, new_player_token
from backend.app.services.business_market import (
    get_business_price,
    get_buyable_businesses,
    process_business_dividend_collection,
    process_business_purchase,
)
from backend.app.services.building_applications import create_building_application
from backend.app.services.buildings import activate_building_application
from backend.app.services.economy import game_day_tick, process_rent_payment, process_shift_work, update_inflation_rate
from backend.app.services.education import load_manager_exam, process_exam_submission
from backend.app.services.ids import to_uuid, try_uuid
from backend.app.services.idempotency import get_idempotent_response, save_idempotent_response
from backend.app.services.city_news import build_city_news, build_day_tick_news
from backend.app.services.city_districts import get_city_districts
from backend.app.services.land import get_land_parcels, process_land_purchase
from backend.app.services.job_queries import education_rank, get_active_job, get_job, get_vacant_jobs
from backend.app.services.messages import INVALID_PLAYER_SESSION_MESSAGE, JOB_NOT_FOUND_MESSAGE
from backend.app.services.needs import process_meal_purchase
from backend.app.services.player_profile import build_player_snapshot, get_player_snapshot
from backend.app.services.player_progress import build_goal_effects
from backend.app.services.sports import sign_athlete_contract, train_at_gym

router = APIRouter(prefix="/api", tags=["mvp"])


class PlayerRegister(BaseModel):
    username: str


class JobApply(BaseModel):
    player_id: str
    job_id: str


class BusinessBuy(BaseModel):
    player_id: str
    business_id: str


class BusinessDividend(BaseModel):
    player_id: str
    business_id: str


class LandBuy(BaseModel):
    player_id: str
    land_parcel_id: str


class BuildingApplicationCreate(BaseModel):
    player_id: str
    land_parcel_id: str
    proposed_name: str
    project_type: str
    expected_jobs: int = 0
    traffic_load: int = 0
    service_load: int = 0
    medical_load: int = 0
    public_benefit: int = 0


class BuildingApplicationActivate(BaseModel):
    player_id: str


class SportsContractJoin(BaseModel):
    player_id: str
    club_id: str


class SportsTrain(BaseModel):
    player_id: str
    stat_type: str


class ExamAnswers(BaseModel):
    player_id: str
    answers: Dict[str, int]


def require_player(db: Session, player_id: str, player_token: str | None) -> Player | None:
    return get_authorized_player(db, player_id, player_token)


def land_parcel_item(parcel: LandParcel) -> LandParcelItem:
    return LandParcelItem(
        id=str(parcel.id),
        city_id=str(parcel.city_id),
        district_id=str(parcel.district_id),
        district_code=parcel.district.code,
        district_name=parcel.district.name,
        code=parcel.code,
        label=parcel.label,
        land_type=parcel.land_type,
        zoning_type=parcel.zoning_type,
        area_hectares=float(parcel.area_hectares),
        base_price_per_hectare=float(parcel.base_price_per_hectare),
        current_price=float(parcel.current_price),
        status=parcel.status,
        owner_player_id=str(parcel.owner_player_id) if parcel.owner_player_id else None,
    )


def building_application_data(application: BuildingApplication) -> BuildingApplicationData:
    return BuildingApplicationData(
        id=str(application.id),
        city_id=str(application.city_id),
        district_id=str(application.district_id),
        land_parcel_id=str(application.land_parcel_id),
        applicant_player_id=str(application.applicant_player_id),
        proposed_name=application.proposed_name,
        project_type=application.project_type,
        land_area_hectares=float(application.land_area_hectares),
        expected_jobs=application.expected_jobs,
        traffic_load=application.traffic_load,
        service_load=application.service_load,
        medical_load=application.medical_load,
        public_benefit=application.public_benefit,
        status=application.status,
        mayor_score=application.mayor_score,
        mayor_summary=application.mayor_summary,
        mayor_issues=[
            MayorPolicyIssueData(code=issue.get("code", ""), message=issue.get("message", ""))
            for issue in application.mayor_issues
        ],
        mayor_questions=list(application.mayor_questions),
    )


def building_item(building: Building) -> BuildingItem:
    return BuildingItem(
        id=str(building.id),
        city_id=str(building.city_id),
        district_id=str(building.district_id),
        land_parcel_id=str(building.land_parcel_id),
        source_application_id=str(building.source_application_id),
        owner_player_id=str(building.owner_player_id),
        name=building.name,
        project_type=building.project_type,
        status=building.status,
        operating_status=building.operating_status,
    )


@router.get("/city/status")
def get_city_status(db: Session = Depends(get_db)):
    city = db.query(City).first()
    if not city:
        raise HTTPException(status_code=404, detail="Місто не знайдене")

    update_inflation_rate(db, city.id)
    data = CityStatusData(
        id=str(city.id),
        name=city.name,
        treasury_balance=float(city.treasury_balance),
        tax_rate_income=float(city.tax_rate_income),
        tax_rate_property=float(city.tax_rate_property),
        inflation_rate=float(city.inflation_rate),
        news=build_city_news(db, city),
        districts=[
            CityDistrictItem(
                id=str(district.id),
                code=district.code,
                name=district.name,
                zone_type=district.zone_type,
                description=district.description,
                display_order=district.display_order,
                land_available_hectares=float(district.land_available_hectares),
                rent_level=district.rent_level,
                job_supply=district.job_supply,
                crime_risk=district.crime_risk,
                traffic=district.traffic,
                service_coverage=district.service_coverage,
                medical_coverage=district.medical_coverage,
                land_value=district.land_value,
                desirability=district.desirability,
            )
            for district in get_city_districts(db, city.id)
        ],
    )
    return api_success("Статус міста оновлено.", data.model_dump())


@router.get("/land/parcels")
def get_public_land_parcels(db: Session = Depends(get_db)):
    city = db.query(City).first()
    if not city:
        return api_error("Місто не знайдене.")

    data = LandParcelsData(parcels=[land_parcel_item(parcel) for parcel in get_land_parcels(db, city.id)])
    return api_success("Доступні земельні ділянки.", data.model_dump())


@router.post("/land/buy")
def buy_land_parcel(
    data: LandBuy,
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
):
    player = require_player(db, data.player_id, player_token)
    if not player:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)

    cached = get_idempotent_response(db, "land_buy", idempotency_key, data.player_id)
    if cached:
        return cached

    land_parcel_uuid = try_uuid(data.land_parcel_id)
    if land_parcel_uuid is None:
        return api_error("Ділянку не знайдено.")

    res = process_land_purchase(db, data.player_id, str(land_parcel_uuid))
    if not res["success"]:
        return api_error(res["message"])

    db.refresh(player)
    return save_player_action_response(
        db,
        "land_buy",
        idempotency_key,
        data.player_id,
        player,
        res["message"],
        LandPurchaseActionData,
        land_parcel=land_parcel_item(res["land_parcel"]),
    )


@router.post("/building/applications")
def submit_building_application(
    data: BuildingApplicationCreate,
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
):
    player = require_player(db, data.player_id, player_token)
    if not player:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)

    cached = get_idempotent_response(db, "building_application", idempotency_key, data.player_id)
    if cached:
        return cached

    land_parcel_uuid = try_uuid(data.land_parcel_id)
    if land_parcel_uuid is None:
        return api_error("Ділянку не знайдено.")

    res = create_building_application(
        db,
        player,
        land_parcel_uuid,
        proposed_name=data.proposed_name,
        project_type=data.project_type,
        expected_jobs=data.expected_jobs,
        traffic_load=data.traffic_load,
        service_load=data.service_load,
        medical_load=data.medical_load,
        public_benefit=data.public_benefit,
    )
    if not res["success"]:
        return api_error(res["message"])

    response = api_success(
        res["message"],
        building_application_data(res["application"]).model_dump(),
    )
    return save_idempotent_response(db, "building_application", idempotency_key, data.player_id, response)


@router.post("/building/applications/{application_id}/activate")
def activate_approved_building_application(
    application_id: str,
    data: BuildingApplicationActivate,
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
):
    player = require_player(db, data.player_id, player_token)
    if not player:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)

    cached = get_idempotent_response(db, "building_application_activate", idempotency_key, data.player_id)
    if cached:
        return cached

    application_uuid = try_uuid(application_id)
    if application_uuid is None:
        return api_error("Будівельну заявку не знайдено.")

    res = activate_building_application(db, player, application_uuid)
    if not res["success"]:
        return api_error(res["message"])

    db.refresh(player)
    return save_player_action_response(
        db,
        "building_application_activate",
        idempotency_key,
        data.player_id,
        player,
        res["message"],
        BuildingActivationActionData,
        building=building_item(res["building"]),
    )


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
    data = DayTickData(city=res["city"], stats=res["stats"], news=build_day_tick_news(res["stats"]))
    return api_success(res["message"], data.model_dump())


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
        hunger=0,
        education_level="High School",
        auth_token=new_player_token(),
    )
    db.add(player)
    db.commit()
    db.refresh(player)

    free_room = db.query(Hostel).filter(Hostel.tenant_player_id.is_(None)).first()
    if free_room:
        free_room.tenant_player_id = player.id
        db.commit()

    snapshot = build_player_snapshot(db, player)
    snapshot["auth_token"] = player.auth_token
    effects = build_goal_effects(db, player)
    hostel_msg = snapshot["hostel"]
    return api_success(
        f"Ласкаво просимо, {username}! Вас поселено: {hostel_msg}.",
        snapshot,
        effects,
    )


@router.get("/player/{player_id}")
def get_player_status(
    player_id: str,
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    db: Session = Depends(get_db),
):
    if not require_player(db, player_id, player_token):
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)

    snapshot = get_player_snapshot(db, player_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Гравця не знайдено")
    return api_success("Статус гравця.", snapshot, snapshot.get("goal_effects", []))


@router.get("/jobs/vacancies")
def get_vacancies(db: Session = Depends(get_db)):
    vacancies = get_vacant_jobs(db)
    data = VacanciesData(
        vacancies=[
            VacancyItem(
                id=str(j.id),
                business_name=j.business.name,
                title=j.title,
                salary_per_hour=float(j.salary_per_hour),
                min_education=j.min_education,
                energy_cost=j.energy_cost_per_shift,
            )
            for j in vacancies
        ]
    )
    return api_success("Доступні вакансії.", data.model_dump())


@router.get("/businesses/market")
def get_business_market(db: Session = Depends(get_db)):
    businesses = get_buyable_businesses(db)
    data = BusinessMarketData(
        businesses=[
            BusinessMarketItem(
                id=str(b.id),
                name=b.name,
                type=b.type,
                cash_balance=float(b.cash_balance),
                purchase_price=float(get_business_price(b)),
            )
            for b in businesses
        ]
    )
    return api_success("Бізнеси для купівлі.", data.model_dump())


@router.post("/businesses/buy")
def buy_business(
    data: BusinessBuy,
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
):
    player = require_player(db, data.player_id, player_token)
    if not player:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)

    cached = get_idempotent_response(db, "business_buy", idempotency_key, data.player_id)
    if cached:
        return cached

    business_uuid = try_uuid(data.business_id)
    if business_uuid is None:
        return api_error("Бізнес не знайдено")

    res = process_business_purchase(db, data.player_id, str(business_uuid))
    if not res["success"]:
        return api_error(res["message"])

    db.refresh(player)
    return save_player_action_response(
        db,
        "business_buy",
        idempotency_key,
        data.player_id,
        player,
        res["message"],
        BusinessBuyActionData,
        business=res["business"],
    )


@router.post("/businesses/dividend")
def collect_business_dividend(
    data: BusinessDividend,
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
):
    player = require_player(db, data.player_id, player_token)
    if not player:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)

    cached = get_idempotent_response(db, "business_dividend", idempotency_key, data.player_id)
    if cached:
        return cached

    business_uuid = try_uuid(data.business_id)
    if business_uuid is None:
        return api_error("Бізнес не знайдено")

    res = process_business_dividend_collection(db, data.player_id, str(business_uuid))
    if not res["success"]:
        return api_error(res["message"])

    db.refresh(player)
    return save_player_action_response(
        db,
        "business_dividend",
        idempotency_key,
        data.player_id,
        player,
        res["message"],
        BusinessDividendActionData,
        business=res["business"],
        dividend=res["dividend"],
    )


@router.get("/sports/clubs")
def get_mvp_sports_clubs(db: Session = Depends(get_db)):
    clubs = db.query(SportsClub).order_by(SportsClub.name).all()
    data = SportsClubsData(
        clubs=[
            SportsClubItem(
                id=str(c.id),
                name=c.name,
                sport_type=c.sport_type,
                salary_per_match=120.0,
                league_points=c.league_points,
            )
            for c in clubs
        ]
    )
    return api_success("Доступні спортивні клуби.", data.model_dump())


@router.post("/sports/join")
def join_sports_club(
    data: SportsContractJoin,
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
):
    player = require_player(db, data.player_id, player_token)
    if not player:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)

    cached = get_idempotent_response(db, "sports_join", idempotency_key, data.player_id)
    if cached:
        return cached

    club_uuid = try_uuid(data.club_id)
    if club_uuid is None:
        return api_error("Спортивний клуб не знайдено")

    res = sign_athlete_contract(db, data.player_id, str(club_uuid), 120.0)
    if not res["success"]:
        return api_error(res["message"])

    db.refresh(player)
    return save_player_action_response(db, "sports_join", idempotency_key, data.player_id, player, res["message"])


@router.post("/sports/train")
def train_sports(
    data: SportsTrain,
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
):
    player = require_player(db, data.player_id, player_token)
    if not player:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)

    cached = get_idempotent_response(db, "sports_train", idempotency_key, data.player_id)
    if cached:
        return cached

    res = train_at_gym(db, data.player_id, data.stat_type)
    if not res["success"]:
        return api_error(res["message"])

    db.refresh(player)
    return save_player_action_response(
        db,
        "sports_train",
        idempotency_key,
        data.player_id,
        player,
        res["message"],
        SportsTrainActionData,
        sports_stats=res["stats"],
    )


@router.post("/jobs/apply")
def apply_for_job(
    data: JobApply,
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    db: Session = Depends(get_db),
):
    player = require_player(db, data.player_id, player_token)
    if not player:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)

    job_uuid = try_uuid(data.job_id)
    if job_uuid is None:
        return api_error(JOB_NOT_FOUND_MESSAGE)

    job = get_job(db, job_uuid)

    if not job:
        return api_error(JOB_NOT_FOUND_MESSAGE)

    if job.filled_by_player_id is not None:
        return api_error("Ця вакансія вже зайнята.")

    player_rank = education_rank(player.education_level)
    required_rank = education_rank(job.min_education)

    if player_rank < required_rank:
        return api_error(
            f"Недостатня освіта! Потрібно '{job.min_education}', у вас '{player.education_level}'.",
            {"required_education": job.min_education},
        )

    old_job = get_active_job(db, player.id)
    if old_job:
        old_job.filled_by_player_id = None
        db.flush()

    job.filled_by_player_id = player.id
    db.commit()

    return build_player_action_response(db, player, f"Вас працевлаштовано на '{job.title}'.")


@router.post("/jobs/work/{player_id}")
def do_work_shift(
    player_id: str,
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
):
    if not require_player(db, player_id, player_token):
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)

    cached = get_idempotent_response(db, "work_shift", idempotency_key, player_id)
    if cached:
        return cached

    res = process_shift_work(db, player_id)
    if not res["success"]:
        return api_error(res["message"])

    player = db.query(Player).filter(Player.id == to_uuid(player_id)).first()
    return save_player_action_response(
        db,
        "work_shift",
        idempotency_key,
        player_id,
        player,
        res["message"],
        WorkActionData,
        city=res.get("city", {}),
    )


@router.post("/hostels/sleep/{player_id}")
def sleep_in_hostel(
    player_id: str,
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
):
    if not require_player(db, player_id, player_token):
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)

    cached = get_idempotent_response(db, "sleep", idempotency_key, player_id)
    if cached:
        return cached

    res = process_rent_payment(db, player_id)
    if not res["success"]:
        return api_error(res["message"])

    player = db.query(Player).filter(Player.id == to_uuid(player_id)).first()
    return save_player_action_response(db, "sleep", idempotency_key, player_id, player, res["message"])


@router.post("/needs/eat/{player_id}")
def eat_meal(
    player_id: str,
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
):
    if not require_player(db, player_id, player_token):
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)

    cached = get_idempotent_response(db, "eat", idempotency_key, player_id)
    if cached:
        return cached

    res = process_meal_purchase(db, player_id)
    if not res["success"]:
        return api_error(res["message"])

    player = db.query(Player).filter(Player.id == to_uuid(player_id)).first()
    return save_player_action_response(db, "eat", idempotency_key, player_id, player, res["message"])


@router.get("/education/exam/info")
def get_exam_details():
    exam = load_manager_exam()
    if not exam:
        raise HTTPException(status_code=404, detail="Файл квізу не знайдено на сервері")

    clean_exam = ExamInfoData(
        exam_id=exam["exam_id"],
        title=exam["title"],
        cost_to_take=exam["cost_to_take"],
        passing_score=exam["passing_score"],
        time_limit_seconds=exam["time_limit_seconds"],
        description=exam["description"],
        questions=[
            ExamQuestionData(id=q["id"], text=q["text"], options=q["options"])
            for q in exam["questions"]
        ],
    )
    return api_success("Інформація про іспит.", clean_exam.model_dump())


@router.post("/education/exam/submit")
def submit_exam(
    data: ExamAnswers,
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
):
    if not require_player(db, data.player_id, player_token):
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)

    cached = get_idempotent_response(db, "exam_submit", idempotency_key, data.player_id)
    if cached:
        return cached

    res = process_exam_submission(db, data.player_id, data.answers)
    if not res["success"]:
        return api_error(res["message"])

    player = db.query(Player).filter(Player.id == to_uuid(data.player_id)).first()
    return save_player_action_response(
        db,
        "exam_submit",
        idempotency_key,
        data.player_id,
        player,
        res["message"],
        ExamSubmitActionData,
        passed=res.get("passed"),
        score=res.get("score"),
        details=res.get("details", []),
    )

from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.api.responses import (
    build_player_action_response,
    save_player_action_response,
)
from backend.app.core.config import settings
from backend.app.database import get_db
from backend.app.models import (
    Building,
    BuildingApplication,
    Business,
    BusinessBlueprint,
    City,
    CityDistrict,
    Job,
    LandParcel,
    Player,
    SportsClub,
)
from backend.app.schemas.mvp import (
    AvatarCatalogData,
    BuildingActivationActionData,
    BuildingApplicationData,
    BuildingItem,
    BuildingOpenActionData,
    BuildingPortfolioData,
    BuildingPortfolioItem,
    BuildingRepairActionData,
    BusinessBlueprintItem,
    BusinessBlueprintsData,
    BusinessBuyActionData,
    BusinessDividendActionData,
    BusinessMarketData,
    BusinessMarketItem,
    CityDistrictItem,
    CityStatusData,
    DayTickData,
    ExamInfoData,
    ExamQuestionData,
    ExamSubmitActionData,
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
from backend.app.services.auth import get_authorized_player, new_player_token_pair
from backend.app.services.avatar_profile import (
    build_avatar_catalog,
    create_player_avatar,
    validate_avatar_selection,
)
from backend.app.services.building_applications import create_building_application
from backend.app.services.buildings import (
    activate_building_application,
    get_building_available_actions,
    get_building_opening_fee,
    get_building_repair_fee,
    get_building_upkeep_daily,
    get_player_building_portfolio,
    open_building_operations,
    repair_building_operations,
)
from backend.app.services.business_blueprints import get_active_business_blueprints
from backend.app.services.business_market import (
    get_business_price,
    get_buyable_businesses,
    process_business_dividend_collection,
    process_business_purchase,
)
from backend.app.services.city_districts import get_city_districts
from backend.app.services.city_news import build_city_news, build_day_tick_news
from backend.app.services.economy import (
    game_day_tick,
    process_rent_payment,
    process_shift_work,
    update_inflation_rate,
)
from backend.app.services.education import load_manager_exam, process_exam_submission
from backend.app.services.idempotency import (
    get_idempotent_response,
    save_idempotent_response,
)
from backend.app.services.ids import to_uuid, try_uuid
from backend.app.services.job_queries import (
    education_rank,
    get_active_job,
    get_job,
    get_vacant_jobs,
)
from backend.app.services.land import get_land_parcels, process_land_purchase
from backend.app.services.messages import (
    INVALID_PLAYER_SESSION_MESSAGE,
    JOB_NOT_FOUND_MESSAGE,
)
from backend.app.services.needs import process_meal_purchase
from backend.app.services.onboarding import (
    ONBOARDING_REQUIRED_MESSAGE,
    build_onboarding_snapshot,
    choose_onboarding_path,
    claim_police_recovery,
    create_player_onboarding,
    is_onboarding_complete,
    random_starting_cash,
)
from backend.app.services.player_profile import (
    build_player_snapshot,
    get_player_snapshot,
)
from backend.app.services.player_progress import build_goal_effects
from backend.app.services.sports import sign_athlete_contract, train_at_gym

router = APIRouter(prefix="/api", tags=["mvp"])


class AvatarCreateSelection(BaseModel):
    body_preset_code: str = "body_standard"
    face_preset_code: str = "face_01"
    skin_tone_code: str = "skin_03"
    hair_style_code: str = "hair_short_01"
    hair_color_code: str = "hair_brown"


class PlayerRegister(BaseModel):
    username: str
    tutorial_age_group: Literal["teen", "adult", "mature"] = "adult"
    avatar: AvatarCreateSelection = Field(default_factory=AvatarCreateSelection)


class OnboardingChoice(BaseModel):
    player_id: str
    choice: str


class OnboardingClaim(BaseModel):
    player_id: str


class JobApply(BaseModel):
    player_id: str
    job_id: str | None = None
    vacancy_id: str | None = None

    @property
    def resolved_job_id(self) -> str | None:
        return self.job_id or self.vacancy_id


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
    business_blueprint_id: str | None = None
    proposed_name: str = ""
    project_type: str = ""
    expected_jobs: int = 0
    traffic_load: int = 0
    service_load: int = 0
    medical_load: int = 0
    public_benefit: int = 0


class BuildingApplicationActivate(BaseModel):
    player_id: str


class BuildingOpen(BaseModel):
    player_id: str


class BuildingRepair(BaseModel):
    player_id: str


class SportsContractJoin(BaseModel):
    player_id: str
    club_id: str


class SportsTrain(BaseModel):
    player_id: str
    stat_type: str


class ExamAnswers(BaseModel):
    player_id: str
    answers: dict[str, int]


def require_player(db: Session, player_id: str, player_token: str | None) -> Player | None:
    return get_authorized_player(db, player_id, player_token)


def require_completed_onboarding(db: Session, player: Player) -> dict | None:
    if is_onboarding_complete(db, player):
        return None
    return api_error(
        ONBOARDING_REQUIRED_MESSAGE,
        {"onboarding": build_onboarding_snapshot(db, player)},
    )


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


def building_application_data(
    application: BuildingApplication,
) -> BuildingApplicationData:
    return BuildingApplicationData(
        id=str(application.id),
        city_id=str(application.city_id),
        district_id=str(application.district_id),
        land_parcel_id=str(application.land_parcel_id),
        business_blueprint_id=str(application.business_blueprint_id) if application.business_blueprint_id else None,
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
        business_blueprint_id=str(building.business_blueprint_id) if building.business_blueprint_id else None,
        business_id=str(building.business_id) if building.business_id else None,
        owner_player_id=str(building.owner_player_id),
        name=building.name,
        project_type=building.project_type,
        status=building.status,
        operating_status=building.operating_status,
    )


def building_portfolio_item(building: Building) -> BuildingPortfolioItem:
    blueprint = building.business_blueprint
    business = building.business
    return BuildingPortfolioItem(
        id=str(building.id),
        city_id=str(building.city_id),
        district_id=str(building.district_id),
        district_code=building.district.code,
        district_name=building.district.name,
        land_parcel_id=str(building.land_parcel_id),
        land_parcel_code=building.land_parcel.code,
        land_parcel_label=building.land_parcel.label,
        source_application_id=str(building.source_application_id),
        business_blueprint_id=str(building.business_blueprint_id) if building.business_blueprint_id else None,
        blueprint_code=blueprint.code if blueprint else None,
        blueprint_name=blueprint.name if blueprint else None,
        blueprint_category=blueprint.category if blueprint else None,
        business_id=str(building.business_id) if building.business_id else None,
        business_type=business.type if business else (blueprint.business_type if blueprint else None),
        business_cash_balance=float(business.cash_balance) if business else None,
        owner_player_id=str(building.owner_player_id),
        name=building.name,
        project_type=building.project_type,
        status=building.status,
        operating_status=building.operating_status,
        opening_fee=float(get_building_opening_fee(building)),
        repair_fee=float(get_building_repair_fee(building)),
        upkeep_daily=float(get_building_upkeep_daily(building)),
        available_actions=get_building_available_actions(building),
    )


def business_blueprint_item(blueprint: BusinessBlueprint) -> BusinessBlueprintItem:
    return BusinessBlueprintItem(
        id=str(blueprint.id),
        code=blueprint.code,
        name=blueprint.name,
        category=blueprint.category,
        business_type=blueprint.business_type,
        project_type=blueprint.project_type,
        description=blueprint.description,
        difficulty=blueprint.difficulty,
        allowed_land_types=list(blueprint.allowed_land_types or []),
        allowed_zoning_types=list(blueprint.allowed_zoning_types or []),
        min_area_hectares=float(blueprint.min_area_hectares),
        construction_cost=float(blueprint.construction_cost),
        opening_fee=float(blueprint.opening_fee),
        recommended_cash_reserve=float(blueprint.recommended_cash_reserve),
        daily_profit_min=float(blueprint.daily_profit_min),
        daily_profit_max=float(blueprint.daily_profit_max),
        upkeep_daily=float(blueprint.upkeep_daily),
        risk_level=blueprint.risk_level,
        risks=list(blueprint.risks or []),
        metric_effects={key: int(value) for key, value in (blueprint.metric_effects or {}).items()},
        visual_archetype=blueprint.visual_archetype,
        style_tags=list(blueprint.style_tags or []),
        player_hints=list(blueprint.player_hints or []),
    )


@router.get("/city/status")
async def get_city_status(db: Session = Depends(get_db)):
    from backend.app.core.redis import CacheService

    city = db.query(City).first()
    if not city:
        raise HTTPException(status_code=404, detail="Місто не знайдене")

    # Спробуємо отримати з кешу
    cache_key = CacheService.make_city_key(str(city.id))
    cached_data = await CacheService.get(cache_key)

    if cached_data:
        return api_success("Статус міста (з кешу).", cached_data)

    # Якщо немає в кеші, генеруємо дані
    update_inflation_rate(db, city.id)
    data = CityStatusData(
        id=str(city.id),
        name=city.name,
        game_day=city.game_day or 1,
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

    # Зберігаємо в кеш на 1 хвилину
    data_dict = data.model_dump()
    await CacheService.set(cache_key, data_dict, CacheService.TTL_CITY_STATUS)

    return api_success("Статус міста оновлено.", data_dict)


@router.get("/land/parcels")
def get_public_land_parcels(db: Session = Depends(get_db)):
    city = db.query(City).first()
    if not city:
        return api_error("Місто не знайдене.")

    data = LandParcelsData(parcels=[land_parcel_item(parcel) for parcel in get_land_parcels(db, city.id)])
    return api_success("Доступні земельні ділянки.", data.model_dump())


@router.get("/business/blueprints")
def get_business_blueprints(db: Session = Depends(get_db)):
    data = BusinessBlueprintsData(
        blueprints=[business_blueprint_item(blueprint) for blueprint in get_active_business_blueprints(db)]
    )
    return api_success("Доступні бізнес-шаблони.", data.model_dump())


@router.get("/avatar/catalog")
def get_avatar_catalog():
    data = AvatarCatalogData.model_validate(build_avatar_catalog())
    return api_success("Доступні складові персонажа.", data.model_dump())


@router.get("/districts/{district_id}/radar")
def get_district_radar(district_id: str, db: Session = Depends(get_db)):
    """Phase G1: композитні індекси району (0-100) + тренд за 7 днів."""
    from backend.app.services.district_metrics import get_radar_with_trend

    district_uuid = try_uuid(district_id)
    if district_uuid is None:
        return api_error("Невірний ідентифікатор району.")

    district = db.query(CityDistrict).filter(CityDistrict.id == district_uuid).first()
    if not district:
        return api_error("Район не знайдено.")

    radar = get_radar_with_trend(db, district_uuid)
    return api_success("Радар метрик району.", radar)


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
    onboarding_error = require_completed_onboarding(db, player)
    if onboarding_error:
        return onboarding_error

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
    onboarding_error = require_completed_onboarding(db, player)
    if onboarding_error:
        return onboarding_error

    cached = get_idempotent_response(db, "building_application", idempotency_key, data.player_id)
    if cached:
        return cached

    land_parcel_uuid = try_uuid(data.land_parcel_id)
    if land_parcel_uuid is None:
        return api_error("Ділянку не знайдено.")

    blueprint_uuid = None
    if data.business_blueprint_id:
        blueprint_uuid = try_uuid(data.business_blueprint_id)
        if blueprint_uuid is None:
            return api_error("Бізнес-шаблон не знайдено.")

    res = create_building_application(
        db,
        player,
        land_parcel_uuid,
        business_blueprint_id=blueprint_uuid,
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
    onboarding_error = require_completed_onboarding(db, player)
    if onboarding_error:
        return onboarding_error

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


@router.post("/buildings/{building_id}/open")
def open_building(
    building_id: str,
    data: BuildingOpen,
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
):
    player = require_player(db, data.player_id, player_token)
    if not player:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    onboarding_error = require_completed_onboarding(db, player)
    if onboarding_error:
        return onboarding_error

    cached = get_idempotent_response(db, "building_open", idempotency_key, data.player_id)
    if cached:
        return cached

    building_uuid = try_uuid(building_id)
    if building_uuid is None:
        return api_error("Будівлю не знайдено.")

    res = open_building_operations(db, player, building_uuid)
    if not res["success"]:
        return api_error(res["message"])

    db.refresh(player)
    return save_player_action_response(
        db,
        "building_open",
        idempotency_key,
        data.player_id,
        player,
        res["message"],
        BuildingOpenActionData,
        building=building_item(res["building"]),
        opening_fee=res["opening_fee"],
    )


@router.post("/buildings/{building_id}/repair")
def repair_building(
    building_id: str,
    data: BuildingRepair,
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
):
    player = require_player(db, data.player_id, player_token)
    if not player:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    onboarding_error = require_completed_onboarding(db, player)
    if onboarding_error:
        return onboarding_error

    cached = get_idempotent_response(db, "building_repair", idempotency_key, data.player_id)
    if cached:
        return cached

    building_uuid = try_uuid(building_id)
    if building_uuid is None:
        return api_error("Будівлю не знайдено.")

    res = repair_building_operations(db, player, building_uuid)
    if not res["success"]:
        return api_error(res["message"])

    db.refresh(player)
    return save_player_action_response(
        db,
        "building_repair",
        idempotency_key,
        data.player_id,
        player,
        res["message"],
        BuildingRepairActionData,
        building=building_item(res["building"]),
        repair_fee=res["repair_fee"],
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
    if len(username) < 2 or len(username) > 24:
        return api_error("Ім'я має містити від 2 до 24 символів.")

    existing = db.query(Player).filter(Player.username == username).first()
    if existing:
        return api_error("Громадянин з таким ім'ям вже зареєстрований.")

    avatar_selection = data.avatar.model_dump()
    avatar_error = validate_avatar_selection(avatar_selection)
    if avatar_error:
        return api_error(avatar_error)

    city = db.query(City).first()
    if not city:
        return api_error("Місто ще не ініціалізоване.")

    player_token, player_token_hash = new_player_token_pair()
    player = Player(
        city_id=city.id,
        username=username,
        balance=random_starting_cash(),
        energy=100,
        mood=100,
        hunger=0,
        tutorial_age_group=data.tutorial_age_group,
        education_level="High School",
        auth_token_hash=player_token_hash,
    )
    db.add(player)
    db.flush()
    create_player_avatar(db, player, avatar_selection)
    create_player_onboarding(db, player)
    db.commit()
    db.refresh(player)

    snapshot = build_player_snapshot(db, player)
    snapshot["auth_token"] = player_token
    effects = build_goal_effects(db, player)
    return api_success(
        f"Ласкаво просимо, {username}. Ви прибули на автовокзал нового міста.",
        snapshot,
        effects,
    )


@router.get("/player/{player_id}/onboarding")
def get_onboarding_status(
    player_id: str,
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    db: Session = Depends(get_db),
):
    player = require_player(db, player_id, player_token)
    if not player:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    return api_success("Стан прибуття.", build_onboarding_snapshot(db, player))


@router.post("/player/onboarding/choose")
def choose_arrival_path(
    data: OnboardingChoice,
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
):
    player = require_player(db, data.player_id, player_token)
    if not player:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)

    cached = get_idempotent_response(db, "onboarding_choose", idempotency_key, data.player_id)
    if cached:
        return cached

    res = choose_onboarding_path(db, player, data.choice)
    if not res["success"]:
        return api_error(res["message"])

    db.refresh(player)
    return save_player_action_response(
        db,
        "onboarding_choose",
        idempotency_key,
        data.player_id,
        player,
        res["message"],
    )


@router.post("/player/onboarding/police-recovery")
def collect_police_recovery(
    data: OnboardingClaim,
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
):
    player = require_player(db, data.player_id, player_token)
    if not player:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)

    cached = get_idempotent_response(db, "onboarding_police_recovery", idempotency_key, data.player_id)
    if cached:
        return cached

    res = claim_police_recovery(db, player)
    if not res["success"]:
        return api_error(res["message"])

    db.refresh(player)
    return save_player_action_response(
        db,
        "onboarding_police_recovery",
        idempotency_key,
        data.player_id,
        player,
        res["message"],
    )


@router.get("/player/{player_id}/buildings")
def get_player_buildings(
    player_id: str,
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    db: Session = Depends(get_db),
):
    player = require_player(db, player_id, player_token)
    if not player:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)

    data = BuildingPortfolioData(
        buildings=[building_portfolio_item(building) for building in get_player_building_portfolio(db, player)]
    )
    return api_success("Будівлі гравця.", data.model_dump())


@router.get("/player/{player_id}")
async def get_player_status(
    player_id: str,
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    db: Session = Depends(get_db),
):
    from backend.app.core.redis import CacheService

    if not require_player(db, player_id, player_token):
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)

    # Спробуємо отримати з кешу (тільки для реальних даних, не для всього snapshot)
    cache_key = CacheService.make_player_realtime_key(player_id)
    cached_data = await CacheService.get(cache_key)

    if cached_data:
        # Якщо є в кешу, використовуємо його
        return api_success("Статус гравця (з кешу).", cached_data, cached_data.get("goal_effects", []))

    snapshot = get_player_snapshot(db, player_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Гравця не знайдено")

    # Кешуємо тільки реальні дані (баланс, енергія, настрій, голод)
    realtime_data = {
        "balance": snapshot.get("balance"),
        "energy": snapshot.get("energy"),
        "mood": snapshot.get("mood"),
        "hunger": snapshot.get("hunger"),
        "current_job": snapshot.get("current_job"),
        "owned_business": snapshot.get("owned_business"),
    }

    # Зберігаємо в кеш на 10 секунд
    await CacheService.set(cache_key, realtime_data, CacheService.TTL_PLAYER_REALTIME)

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
    onboarding_error = require_completed_onboarding(db, player)
    if onboarding_error:
        return onboarding_error

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
    onboarding_error = require_completed_onboarding(db, player)
    if onboarding_error:
        return onboarding_error

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


@router.get("/businesses/{business_id}/npcs")
def list_business_npcs_endpoint(business_id: str, db: Session = Depends(get_db)):
    """Phase G2: список NPC, найнятих у бізнесі."""
    from backend.app.services.npc_service import list_business_npcs, npc_to_dict

    business_uuid = try_uuid(business_id)
    if business_uuid is None:
        return api_error("Невірний ідентифікатор бізнесу.")

    business = db.query(Business).filter(Business.id == business_uuid).first()
    if not business:
        return api_error("Бізнес не знайдено.")

    npcs = list_business_npcs(db, business_uuid)
    return api_success(
        "NPC бізнесу.",
        {"npcs": [npc_to_dict(n) for n in npcs], "count": len(npcs)},
    )


@router.post("/businesses/{business_id}/npcs/hire")
def hire_npc_endpoint(
    business_id: str,
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    db: Session = Depends(get_db),
):
    """Phase G2: найм NPC для бізнесу (власником)."""
    from backend.app.services.npc_service import hire_npc_for_business

    business_uuid = try_uuid(business_id)
    if business_uuid is None:
        return api_error("Невірний ідентифікатор бізнесу.")

    business = db.query(Business).filter(Business.id == business_uuid).first()
    if not business:
        return api_error("Бізнес не знайдено.")

    # Перевірка власника (якщо бізнес має власника — потрібен token).
    # Для муніципальних бізнесів (owner_player_id is None) — дозволено.
    if business.owner_player_id is not None and not player_token:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)

    result = hire_npc_for_business(db, business)
    if not result["success"]:
        return api_error(result["message"])
    db.commit()
    return api_success(result["message"], result)


@router.post("/businesses/{business_id}/npcs/{npc_id}/dismiss")
def dismiss_npc_endpoint(
    business_id: str,
    npc_id: str,
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    db: Session = Depends(get_db),
):
    """Phase G2: звільнення NPC з бізнесу."""
    from backend.app.services.npc_service import dismiss_npc

    business_uuid = try_uuid(business_id)
    if business_uuid is None:
        return api_error("Невірний ідентифікатор бізнесу.")

    npc_uuid = try_uuid(npc_id)
    if npc_uuid is None:
        return api_error("Невірний ідентифікатор NPC.")

    business = db.query(Business).filter(Business.id == business_uuid).first()
    if not business:
        return api_error("Бізнес не знайдено.")

    if business.owner_player_id is not None and not player_token:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)

    dismissed = dismiss_npc(db, npc_uuid)
    if not dismissed:
        return api_error("NPC не знайдено.")
    db.commit()
    return api_success("NPC звільнено.", {"npc_id": npc_id})


@router.get("/city/utility-status")
def get_utility_status_endpoint(db: Session = Depends(get_db)):
    """Phase G3: статус комунальних служб міста + попередження мера."""
    from backend.app.services.utility_service import get_mayor_warnings, get_utility_status

    city = db.query(City).first()
    if not city:
        return api_error("Місто не знайдене.")

    statuses = get_utility_status(db, city.id)
    warnings = get_mayor_warnings(db, city.id)
    return api_success(
        "Статус комунальних служб.",
        {
            "services": [
                {
                    "service_type": s.service_type,
                    "active_businesses": s.active_businesses,
                    "total_capacity": s.total_capacity,
                    "total_load": s.total_load,
                    "load_ratio": round(s.load_ratio, 3),
                    "has_emergency_contract": s.has_emergency_contract,
                    "warnings": s.warnings,
                }
                for s in statuses
            ],
            "mayor_warnings": warnings,
        },
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
    onboarding_error = require_completed_onboarding(db, player)
    if onboarding_error:
        return onboarding_error

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
    onboarding_error = require_completed_onboarding(db, player)
    if onboarding_error:
        return onboarding_error

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
    onboarding_error = require_completed_onboarding(db, player)
    if onboarding_error:
        return onboarding_error

    job_uuid = try_uuid(data.resolved_job_id)
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
async def do_work_shift(
    player_id: str,
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
):
    player = require_player(db, player_id, player_token)
    if not player:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    onboarding_error = require_completed_onboarding(db, player)
    if onboarding_error:
        return onboarding_error

    cached = get_idempotent_response(db, "work_shift", idempotency_key, player_id)
    if cached:
        return cached

    res = process_shift_work(db, player_id)
    if not res["success"]:
        return api_error(res["message"])

    # Інвалідуємо кеш гравця після успішної зміни
    from backend.app.core.redis import invalidate_player_cache

    await invalidate_player_cache(player_id)

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


# --- Phase G4: Vacancies and Hiring ---


@router.get("/vacancies/player")
def list_player_vacancies(db: Session = Depends(get_db)):
    """Phase G4: список відкритих гравець-вакансій (не NPC)."""
    from backend.app.services.vacancy_service import job_to_dict, list_open_vacancies

    city = db.query(City).first()
    city_id = city.id if city else None
    vacancies = list_open_vacancies(db, city_id)
    return api_success(
        "Відкриті вакансії для гравців.",
        {"vacancies": [job_to_dict(j, include_business=True) for j in vacancies]},
    )


@router.get("/vacancies/student")
def list_student_vacancies_endpoint(db: Session = Depends(get_db)):
    """Phase G4: біржа студентських робіт (вечірні зміни)."""
    from backend.app.services.vacancy_service import job_to_dict, list_student_vacancies

    city = db.query(City).first()
    city_id = city.id if city else None
    vacancies = list_student_vacancies(db, city_id)
    return api_success(
        "Студентські вакансії (вечірні зміни).",
        {"vacancies": [job_to_dict(j, include_business=True) for j in vacancies]},
    )


@router.post("/businesses/{business_id}/vacancies")
def post_vacancy_endpoint(
    business_id: str,
    data: dict,
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    db: Session = Depends(get_db),
):
    """Phase G4: власник виставляє вакансію для гравця-працівника."""
    from backend.app.services.vacancy_service import DEFAULT_BONUS_PCT, post_player_vacancy

    business_uuid = try_uuid(business_id)
    if business_uuid is None:
        return api_error("Невірний ідентифікатор бізнесу.")

    business = db.query(Business).filter(Business.id == business_uuid).first()
    if not business:
        return api_error("Бізнес не знайдено.")

    if not player_token:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)

    bonus_pct = Decimal(str(data.get("bonus_pct", DEFAULT_BONUS_PCT)))
    shift_type = data.get("shift_type", "day")
    title = data.get("title")
    min_education = data.get("min_education", "High School")

    result = post_player_vacancy(
        db,
        business,
        title=title,
        bonus_pct=bonus_pct,
        shift_type=shift_type,
        min_education=min_education,
    )
    if not result["success"]:
        return api_error(result["message"])
    db.commit()
    return api_success(result["message"], result)


@router.post("/businesses/{business_id}/owner-work")
def owner_works_endpoint(
    business_id: str,
    data: dict,
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    db: Session = Depends(get_db),
):
    """Phase G4: власник працює у власному бізнесі (витрачає енергію)."""
    from backend.app.services.vacancy_service import owner_works_shift

    business_uuid = try_uuid(business_id)
    if business_uuid is None:
        return api_error("Невірний ідентифікатор бізнесу.")

    business = db.query(Business).filter(Business.id == business_uuid).first()
    if not business:
        return api_error("Бізнес не знайдено.")

    player_uuid = try_uuid(data.get("player_id", ""))
    if player_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)

    player = db.query(Player).filter(Player.id == player_uuid).first()
    if not player:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)

    result = owner_works_shift(db, business, player)
    if not result["success"]:
        return api_error(result["message"])
    db.commit()
    return api_success(result["message"], result)


@router.post("/jobs/{job_id}/fire")
def fire_player_endpoint(
    job_id: str,
    data: dict,
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    db: Session = Depends(get_db),
):
    """Phase G4: власник звільняє гравця-працівника."""
    from backend.app.services.vacancy_service import fire_player

    job_uuid = try_uuid(job_id)
    if job_uuid is None:
        return api_error("Невірний ідентифікатор вакансії.")

    job = db.query(Job).filter(Job.id == job_uuid).first()
    if not job:
        return api_error("Вакансію не знайдено.")

    player_uuid = try_uuid(data.get("player_id", ""))
    if player_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)

    owner = db.query(Player).filter(Player.id == player_uuid).first()
    if not owner:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)

    result = fire_player(db, job, owner)
    if not result["success"]:
        return api_error(result["message"])
    db.commit()
    return api_success(result["message"], {"job_id": job_id})


# --- Phase G10: Education ---


@router.get("/education/courses")
def education_courses_endpoint():
    """Phase G10: каталог курсів."""
    from backend.app.services.education_service import list_courses

    return api_success("Каталог курсів.", {"courses": list_courses()})


@router.post("/education/enroll")
def education_enroll_endpoint(data: dict, db: Session = Depends(get_db)):
    """Phase G10: записатися на курс."""
    from backend.app.services.education_service import enroll

    player_uuid = try_uuid(data.get("player_id", ""))
    if player_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    player = db.query(Player).filter(Player.id == player_uuid).first()
    if not player:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    course = data.get("course", "")
    mode = data.get("mode", "full_time")
    result = enroll(db, player, course, mode)
    if not result["success"]:
        return api_error(result["message"])
    db.commit()
    return api_success(result["message"], result)


@router.get("/education/active")
def education_active_endpoint(player_id: str, db: Session = Depends(get_db)):
    """Phase G10: активні курси гравця."""
    from backend.app.services.education_service import get_active_enrollments

    player_uuid = try_uuid(player_id)
    if player_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    player = db.query(Player).filter(Player.id == player_uuid).first()
    if not player:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    active = get_active_enrollments(db, player)
    return api_success(
        "Активні курси.",
        {
            "active": [
                {
                    "id": str(e.id),
                    "course": e.course,
                    "mode": e.mode,
                    "status": e.status,
                    "is_fake": e.is_fake,
                    "enrolled_at": e.enrolled_at.isoformat() if e.enrolled_at else None,
                }
                for e in active
            ]
        },
    )


@router.get("/education/completed")
def education_completed_endpoint(player_id: str, db: Session = Depends(get_db)):
    """Phase G10: завершені курси гравця."""
    from backend.app.services.education_service import get_completed_courses

    player_uuid = try_uuid(player_id)
    if player_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    player = db.query(Player).filter(Player.id == player_uuid).first()
    if not player:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    completed = get_completed_courses(db, player)
    return api_success(
        "Завершені курси.",
        {
            "completed": [
                {
                    "id": str(e.id),
                    "course": e.course,
                    "mode": e.mode,
                    "is_fake": e.is_fake,
                    "completed_at": e.completed_at.isoformat() if e.completed_at else None,
                }
                for e in completed
            ]
        },
    )


@router.post("/education/complete")
def education_complete_endpoint(data: dict, db: Session = Depends(get_db)):
    """Phase G10: завершити курс (викликається scheduler-ом після duration_days)."""
    from backend.app.models import Education
    from backend.app.services.education_service import complete_education

    edu_uuid = try_uuid(data.get("education_id", ""))
    if edu_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    education = db.query(Education).filter(Education.id == edu_uuid).first()
    if not education:
        return api_error("Курс не знайдено.")
    result = complete_education(db, education)
    if not result["success"]:
        return api_error(result["message"])
    db.commit()
    return api_success(result["message"], result)


@router.post("/education/exam")
def education_exam_endpoint(data: dict, db: Session = Depends(get_db)):
    """Phase G10: скласти іспит (міні-гра)."""
    from backend.app.services.education_service import take_exam

    player_uuid = try_uuid(data.get("player_id", ""))
    if player_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    player = db.query(Player).filter(Player.id == player_uuid).first()
    if not player:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    exam_type = data.get("exam_type", "")
    game_day = int(data.get("game_day", 0))
    result = take_exam(db, player, exam_type, game_day)
    db.commit()
    return api_success(result["message"], result)


@router.post("/education/exam/bribe")
def education_exam_bribe_endpoint(data: dict, db: Session = Depends(get_db)):
    """Phase G10: підкуп іспитуйача (після 2 провалів)."""
    from backend.app.services.education_service import bribe_exam

    player_uuid = try_uuid(data.get("player_id", ""))
    if player_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    player = db.query(Player).filter(Player.id == player_uuid).first()
    if not player:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    exam_type = data.get("exam_type", "")
    result = bribe_exam(db, player, exam_type)
    db.commit()
    return api_success(result["message"], result)


@router.post("/education/license/lawyer")
def education_license_lawyer_endpoint(data: dict, db: Session = Depends(get_db)):
    """Phase G10: ліцензія адвоката."""
    from backend.app.services.education_service import issue_lawyer_license

    player_uuid = try_uuid(data.get("player_id", ""))
    if player_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    player = db.query(Player).filter(Player.id == player_uuid).first()
    if not player:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    result = issue_lawyer_license(db, player)
    if not result["success"]:
        return api_error(result["message"])
    return api_success(result["message"], result)


@router.post("/education/license/police")
def education_license_police_endpoint(data: dict, db: Session = Depends(get_db)):
    """Phase G10: кваліфікація поліцейського."""
    from backend.app.services.education_service import issue_police_qualification

    player_uuid = try_uuid(data.get("player_id", ""))
    if player_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    player = db.query(Player).filter(Player.id == player_uuid).first()
    if not player:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    result = issue_police_qualification(db, player)
    if not result["success"]:
        return api_error(result["message"])
    return api_success(result["message"], result)


@router.post("/education/license/judge")
def education_license_judge_endpoint(data: dict, db: Session = Depends(get_db)):
    """Phase G10: кваліфікація судді."""
    from backend.app.services.education_service import issue_judge_qualification

    player_uuid = try_uuid(data.get("player_id", ""))
    if player_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    player = db.query(Player).filter(Player.id == player_uuid).first()
    if not player:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    result = issue_judge_qualification(db, player)
    if not result["success"]:
        return api_error(result["message"])
    return api_success(result["message"], result)


@router.get("/education/mayor-eligibility")
def education_mayor_eligibility_endpoint(player_id: str, db: Session = Depends(get_db)):
    """Phase G10: перевірка відповідності вимогам мера."""
    from backend.app.services.education_service import check_mayor_eligibility

    player_uuid = try_uuid(player_id)
    if player_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    player = db.query(Player).filter(Player.id == player_uuid).first()
    if not player:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    result = check_mayor_eligibility(db, player)
    return api_success(result["message"], result)


@router.post("/education/fake-diploma")
def education_fake_diploma_endpoint(data: dict, db: Session = Depends(get_db)):
    """Phase G10: купити підробний диплом (тіньова механіка)."""
    from backend.app.services.education_service import buy_fake_diploma

    player_uuid = try_uuid(data.get("player_id", ""))
    if player_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    player = db.query(Player).filter(Player.id == player_uuid).first()
    if not player:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    course = data.get("course", "")
    result = buy_fake_diploma(db, player, course)
    if not result["success"]:
        return api_error(result["message"])
    db.commit()
    return api_success(result["message"], result)


# --- Phase G9: Casino ---


@router.post("/casino/blackjack")
def casino_blackjack_endpoint(data: dict, db: Session = Depends(get_db)):
    """Phase G9: блекджек проти казино."""
    from backend.app.models import Business
    from backend.app.services.casino_service import play_blackjack

    casino_uuid = try_uuid(data.get("casino_id", ""))
    player_uuid = try_uuid(data.get("player_id", ""))
    if casino_uuid is None or player_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    casino = db.query(Business).filter(Business.id == casino_uuid).first()
    player = db.query(Player).filter(Player.id == player_uuid).first()
    if not casino or not player:
        return api_error("Не знайдено.")
    bet = Decimal(str(data.get("bet", 0)))
    result = play_blackjack(db, casino, player, bet)
    db.commit()
    return api_success(result["message"], result)


@router.post("/casino/roulette")
def casino_roulette_endpoint(data: dict, db: Session = Depends(get_db)):
    """Phase G9: рулетка."""
    from backend.app.models import Business
    from backend.app.services.casino_service import play_roulette

    casino_uuid = try_uuid(data.get("casino_id", ""))
    player_uuid = try_uuid(data.get("player_id", ""))
    if casino_uuid is None or player_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    casino = db.query(Business).filter(Business.id == casino_uuid).first()
    player = db.query(Player).filter(Player.id == player_uuid).first()
    if not casino or not player:
        return api_error("Не знайдено.")
    bet = Decimal(str(data.get("bet", 0)))
    bet_type = data.get("bet_type", "red")
    result = play_roulette(db, casino, player, bet, bet_type)
    db.commit()
    return api_success(result["message"], result)


@router.post("/casino/poker/create")
def casino_poker_create_endpoint(data: dict, db: Session = Depends(get_db)):
    """Phase G9: створити покерний стіл."""
    from backend.app.models import Business
    from backend.app.services.casino_service import create_poker_game

    casino_uuid = try_uuid(data.get("casino_id", ""))
    if casino_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    casino = db.query(Business).filter(Business.id == casino_uuid).first()
    if not casino:
        return api_error("Казино не знайдено.")
    min_buyin = Decimal(str(data.get("min_buyin", 100)))
    result = create_poker_game(db, casino, min_buyin)
    if not result["success"]:
        return api_error(result["message"])
    db.commit()
    return api_success(result["message"], result)


@router.post("/casino/tax")
def casino_tax_endpoint(data: dict, db: Session = Depends(get_db)):
    """Phase G9: збір податку з казино (25%)."""
    from backend.app.models import Business
    from backend.app.services.casino_service import collect_casino_tax

    casino_uuid = try_uuid(data.get("casino_id", ""))
    if casino_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    casino = db.query(Business).filter(Business.id == casino_uuid).first()
    city = db.query(City).first()
    if not casino or not city:
        return api_error("Не знайдено.")
    result = collect_casino_tax(db, casino, city)
    db.commit()
    return api_success(result["message"], result)


# --- Phase G9: Atelier ---


@router.post("/atelier/create-skin")
def atelier_create_skin_endpoint(data: dict, db: Session = Depends(get_db)):
    """Phase G9: створити скін."""
    from backend.app.models import Business
    from backend.app.services.atelier_service import create_skin

    designer_uuid = try_uuid(data.get("designer_id", ""))
    atelier_uuid = try_uuid(data.get("atelier_id", ""))
    if designer_uuid is None or atelier_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    designer = db.query(Player).filter(Player.id == designer_uuid).first()
    atelier = db.query(Business).filter(Business.id == atelier_uuid).first()
    if not designer or not atelier:
        return api_error("Не знайдено.")
    result = create_skin(
        db,
        designer,
        atelier,
        data.get("name", "Untitled"),
        data.get("config", {}),
        data.get("rarity", "common"),
        bool(data.get("is_unique", False)),
        int(data.get("copies_total", 1)),
        Decimal(str(data.get("price", 100))),
    )
    if not result["success"]:
        return api_error(result["message"])
    db.commit()
    return api_success(result["message"], result)


@router.post("/atelier/buy-skin")
def atelier_buy_skin_endpoint(data: dict, db: Session = Depends(get_db)):
    """Phase G9: купити скін."""
    from backend.app.models import Business, Skin
    from backend.app.services.atelier_service import buy_skin

    buyer_uuid = try_uuid(data.get("buyer_id", ""))
    skin_uuid = try_uuid(data.get("skin_id", ""))
    atelier_uuid = try_uuid(data.get("atelier_id", ""))
    if buyer_uuid is None or skin_uuid is None or atelier_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    buyer = db.query(Player).filter(Player.id == buyer_uuid).first()
    skin = db.query(Skin).filter(Skin.id == skin_uuid).first()
    atelier = db.query(Business).filter(Business.id == atelier_uuid).first()
    if not buyer or not skin or not atelier:
        return api_error("Не знайдено.")
    result = buy_skin(db, buyer, skin, atelier)
    if not result["success"]:
        return api_error(result["message"])
    db.commit()
    return api_success(result["message"], result)


@router.post("/atelier/equip-skin")
def atelier_equip_skin_endpoint(data: dict, db: Session = Depends(get_db)):
    """Phase G9: надягнути скін."""
    from backend.app.models import PlayerSkin
    from backend.app.services.atelier_service import equip_skin

    player_uuid = try_uuid(data.get("player_id", ""))
    player_skin_uuid = try_uuid(data.get("player_skin_id", ""))
    if player_uuid is None or player_skin_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    player = db.query(Player).filter(Player.id == player_uuid).first()
    player_skin = db.query(PlayerSkin).filter(PlayerSkin.id == player_skin_uuid).first()
    if not player or not player_skin:
        return api_error("Не знайдено.")
    result = equip_skin(db, player, player_skin)
    db.commit()
    return api_success(result["message"], result)


@router.get("/atelier/skins")
def atelier_list_skins_endpoint(atelier_id: str, db: Session = Depends(get_db)):
    """Phase G9: список скінів на продаж."""
    from backend.app.models import Business
    from backend.app.services.atelier_service import list_skins_for_sale

    atelier_uuid = try_uuid(atelier_id)
    if atelier_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    atelier = db.query(Business).filter(Business.id == atelier_uuid).first()
    if not atelier:
        return api_error("Ательє не знайдено.")
    skins = list_skins_for_sale(db, atelier)
    return api_success("Скіни на продажу.", {"skins": skins})


@router.get("/atelier/player-skins")
def atelier_player_skins_endpoint(player_id: str, db: Session = Depends(get_db)):
    """Phase G9: скіни гравця (власні)."""
    from backend.app.services.atelier_service import list_player_skins

    player_uuid = try_uuid(player_id)
    if player_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    player = db.query(Player).filter(Player.id == player_uuid).first()
    if not player:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    skins = list_player_skins(db, player)
    return api_success("Скіни гравця.", {"skins": skins})


@router.post("/atelier/unequip-all")
def atelier_unequip_all_endpoint(data: dict, db: Session = Depends(get_db)):
    """Phase G9: зняти всі скіни."""
    from backend.app.services.atelier_service import unequip_all

    player_uuid = try_uuid(data.get("player_id", ""))
    if player_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    player = db.query(Player).filter(Player.id == player_uuid).first()
    if not player:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    result = unequip_all(db, player)
    db.commit()
    return api_success(result["message"], result)


# --- Phase G9: Shadow ---


@router.post("/shadow/open-business")
def shadow_open_business_endpoint(data: dict, db: Session = Depends(get_db)):
    """Phase G9: відкрити тіньовий бізнес (потрібен criminal_rep >= 30)."""
    from backend.app.models import CityDistrict
    from backend.app.services.shadow_service import open_shadow_business

    player_uuid = try_uuid(data.get("player_id", ""))
    district_uuid = try_uuid(data.get("district_id", ""))
    if player_uuid is None or district_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    player = db.query(Player).filter(Player.id == player_uuid).first()
    district = db.query(CityDistrict).filter(CityDistrict.id == district_uuid).first()
    if not player or not district:
        return api_error("Не знайдено.")
    business_type = data.get("business_type", "illegal_bar")
    result = open_shadow_business(db, player, district, business_type)
    if not result["success"]:
        return api_error(result["message"])
    db.commit()
    return api_success(result["message"], result)


@router.post("/shadow/business-income")
def shadow_business_income_endpoint(data: dict, db: Session = Depends(get_db)):
    """Phase G9: дохід тіньового бізнесу (day tick)."""
    from backend.app.models import ShadowBusiness
    from backend.app.services.shadow_service import shadow_business_income

    business_uuid = try_uuid(data.get("business_id", ""))
    if business_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    business = db.query(ShadowBusiness).filter(ShadowBusiness.id == business_uuid).first()
    if not business:
        return api_error("Тіньовий бізнес не знайдено.")
    game_day = int(data.get("game_day", 0))
    result = shadow_business_income(db, business, game_day)
    db.commit()
    return api_success(result["message"], result)


@router.post("/shadow/check-discovery")
def shadow_check_discovery_endpoint(data: dict, db: Session = Depends(get_db)):
    """Phase G9: перевірка виявлення тіньового бізнесу поліцією."""
    from backend.app.models import Player, ShadowBusiness
    from backend.app.services.shadow_service import check_discovery

    business_uuid = try_uuid(data.get("business_id", ""))
    player_uuid = try_uuid(data.get("player_id", ""))
    if business_uuid is None or player_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    business = db.query(ShadowBusiness).filter(ShadowBusiness.id == business_uuid).first()
    player = db.query(Player).filter(Player.id == player_uuid).first()
    if not business or not player:
        return api_error("Не знайдено.")
    result = check_discovery(db, business, player)
    db.commit()
    return api_success(result["message"], result)


@router.post("/shadow/fraud-offer")
def shadow_fraud_offer_endpoint(data: dict, db: Session = Depends(get_db)):
    """Phase G9: пропозиція шахрайства (day tick)."""
    from backend.app.services.shadow_service import offer_fraud

    player_uuid = try_uuid(data.get("player_id", ""))
    if player_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    player = db.query(Player).filter(Player.id == player_uuid).first()
    if not player:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    game_day = int(data.get("game_day", 0))
    result = offer_fraud(db, player, game_day)
    db.commit()
    return api_success(result["message"], result)


@router.post("/shadow/fraud-accept")
def shadow_fraud_accept_endpoint(data: dict, db: Session = Depends(get_db)):
    """Phase G9: прийняти шахрайство."""
    from backend.app.services.shadow_service import accept_fraud

    player_uuid = try_uuid(data.get("player_id", ""))
    if player_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    player = db.query(Player).filter(Player.id == player_uuid).first()
    if not player:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    amount = Decimal(str(data.get("amount", 0)))
    game_day = int(data.get("game_day", 0))
    result = accept_fraud(db, player, amount, game_day)
    db.commit()
    return api_success(result["message"], result)


@router.post("/shadow/money-laundering")
def shadow_money_laundering_endpoint(data: dict, db: Session = Depends(get_db)):
    """Phase G9: відмивання грошей."""
    from backend.app.services.shadow_service import money_laundering_service

    launderer_uuid = try_uuid(data.get("launderer_id", ""))
    client_uuid = try_uuid(data.get("client_id", ""))
    if launderer_uuid is None or client_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    launderer = db.query(Player).filter(Player.id == launderer_uuid).first()
    client = db.query(Player).filter(Player.id == client_uuid).first()
    if not launderer or not client:
        return api_error("Не знайдено.")
    amount = Decimal(str(data.get("amount", 0)))
    result = money_laundering_service(db, launderer, client, amount)
    db.commit()
    return api_success(result["message"], result)


@router.get("/shadow/market")
def shadow_market_endpoint(player_id: str, db: Session = Depends(get_db)):
    """Phase G9: доступ до тіньового ринку (criminal_rep >= 30)."""
    from backend.app.services.shadow_service import can_access_shadow_market

    player_uuid = try_uuid(player_id)
    if player_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    player = db.query(Player).filter(Player.id == player_uuid).first()
    if not player:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    if not can_access_shadow_market(player):
        return api_error("Доступ до тіньового ринку вимагає criminal_rep >= 30.")
    return api_success(
        "Тіньовий ринок доступний.",
        {
            "criminal_rep": float(player.criminal_rep),
            "items": [
                {"type": "contraband_electronics", "price_modifier": 0.6},
                {"type": "stolen_goods", "price_modifier": 0.5},
                {"type": "fake_medicine", "price_modifier": 0.4},
            ],
        },
    )


# --- Phase G8: Police ---


@router.post("/police/hire")
def police_hire_endpoint(
    data: dict,
    db: Session = Depends(get_db),
):
    """Phase G8: найм гравця в поліцію (patrol)."""
    from backend.app.services.police_service import hire_police_officer

    city = db.query(City).first()
    if not city:
        return api_error("Місто не знайдене.")

    player_uuid = try_uuid(data.get("player_id", ""))
    if player_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    player = db.query(Player).filter(Player.id == player_uuid).first()
    if not player:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)

    game_day = data.get("game_day", 0)
    result = hire_police_officer(db, city, player, game_day)
    if not result["success"]:
        return api_error(result["message"])
    db.commit()
    return api_success(result["message"], result)


@router.post("/police/promote")
def police_promote_endpoint(data: dict, db: Session = Depends(get_db)):
    """Phase G8: підвищення patrol → detective."""
    from backend.app.services.police_service import get_officer, promote_officer

    city = db.query(City).first()
    player_uuid = try_uuid(data.get("player_id", ""))
    if player_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    officer = get_officer(db, city.id, player_uuid)
    if not officer:
        return api_error("Поліцейський не знайдено.")
    result = promote_officer(db, officer, data.get("game_day", 0))
    if not result["success"]:
        return api_error(result["message"])
    db.commit()
    return api_success(result["message"], result)


@router.post("/police/appoint-chief")
def police_appoint_chief_endpoint(data: dict, db: Session = Depends(get_db)):
    """Phase G8: мер призначає начальника поліції."""
    from backend.app.services.police_service import appoint_chief

    city = db.query(City).first()
    mayor_uuid = try_uuid(data.get("mayor_id", ""))
    candidate_uuid = try_uuid(data.get("candidate_id", ""))
    if mayor_uuid is None or candidate_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    mayor = db.query(Player).filter(Player.id == mayor_uuid).first()
    candidate = db.query(Player).filter(Player.id == candidate_uuid).first()
    if not mayor or not candidate:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    result = appoint_chief(db, city, mayor, candidate, data.get("game_day", 0))
    if not result["success"]:
        return api_error(result["message"])
    db.commit()
    return api_success(result["message"], result)


@router.post("/police/patrol")
def police_patrol_endpoint(data: dict, db: Session = Depends(get_db)):
    """Phase G8: патрулювання району."""
    from backend.app.models import CityDistrict
    from backend.app.services.police_service import get_officer, patrol_district

    city = db.query(City).first()
    player_uuid = try_uuid(data.get("player_id", ""))
    district_uuid = try_uuid(data.get("district_id", ""))
    if player_uuid is None or district_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    officer = get_officer(db, city.id, player_uuid)
    if not officer:
        return api_error("Поліцейський не знайдено.")
    district = db.query(CityDistrict).filter(CityDistrict.id == district_uuid).first()
    if not district:
        return api_error("Район не знайдено.")
    result = patrol_district(db, officer, district, data.get("game_day", 0))
    db.commit()
    return api_success(result["message"], result)


@router.post("/police/accept-bribe")
def police_accept_bribe_endpoint(data: dict, db: Session = Depends(get_db)):
    """Phase G8: поліцейський бере хабар."""
    from backend.app.services.police_service import accept_bribe, get_officer

    city = db.query(City).first()
    player_uuid = try_uuid(data.get("player_id", ""))
    if player_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    officer = get_officer(db, city.id, player_uuid)
    player = db.query(Player).filter(Player.id == player_uuid).first()
    if not officer or not player:
        return api_error("Поліцейський не знайдено.")
    amount = Decimal(str(data.get("amount", 0)))
    result = accept_bribe(db, officer, player, amount, data.get("game_day", 0))
    db.commit()
    return api_success(result["message"], result)


@router.post("/police/arrest")
def police_arrest_endpoint(data: dict, db: Session = Depends(get_db)):
    """Phase G8: детектив арештовує гравця."""
    from backend.app.services.police_service import arrest_player, get_officer

    city = db.query(City).first()
    officer_uuid = try_uuid(data.get("officer_id", ""))
    target_uuid = try_uuid(data.get("target_id", ""))
    if officer_uuid is None or target_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    officer = get_officer(db, city.id, officer_uuid)
    target = db.query(Player).filter(Player.id == target_uuid).first()
    if not officer or not target:
        return api_error("Не знайдено.")
    result = arrest_player(db, officer, target, data.get("game_day", 0))
    if not result["success"]:
        return api_error(result["message"])
    db.commit()
    return api_success(result["message"], result)


@router.get("/police/corruption-log")
def police_corruption_log_endpoint(
    player_id: str,
    db: Session = Depends(get_db),
):
    """Phase G8: доступ детектива до corruption_log."""
    from backend.app.services.police_service import get_corruption_log_access, get_officer

    city = db.query(City).first()
    player_uuid = try_uuid(player_id)
    if player_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    officer = get_officer(db, city.id, player_uuid)
    if not officer:
        return api_error("Поліцейський не знайдено.")
    logs = get_corruption_log_access(db, officer, city.id)
    return api_success("Corruption log", {"logs": logs, "rank": officer.rank})


# --- Phase G8: Court ---


@router.post("/court/create-case")
def court_create_case_endpoint(data: dict, db: Session = Depends(get_db)):
    """Phase G8: створення судової справи з corruption_log."""
    from backend.app.models import CorruptionLog
    from backend.app.services.court_service import create_court_case

    corruption_uuid = try_uuid(data.get("corruption_log_id", ""))
    defendant_uuid = try_uuid(data.get("defendant_id", ""))
    if corruption_uuid is None or defendant_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    corruption = db.query(CorruptionLog).filter(CorruptionLog.id == corruption_uuid).first()
    defendant = db.query(Player).filter(Player.id == defendant_uuid).first()
    if not corruption or not defendant:
        return api_error("Не знайдено.")
    result = create_court_case(db, corruption, defendant, data.get("game_day", 0))
    if not result["success"]:
        return api_error(result["message"])
    db.commit()
    return api_success(result["message"], result)


@router.post("/court/appeal")
def court_appeal_endpoint(data: dict, db: Session = Depends(get_db)):
    """Phase G8: подача апеляції."""
    from backend.app.models import CourtCase
    from backend.app.services.court_service import file_appeal

    case_uuid = try_uuid(data.get("case_id", ""))
    player_uuid = try_uuid(data.get("player_id", ""))
    if case_uuid is None or player_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    case = db.query(CourtCase).filter(CourtCase.id == case_uuid).first()
    player = db.query(Player).filter(Player.id == player_uuid).first()
    if not case or not player:
        return api_error("Не знайдено.")
    result = file_appeal(db, case, player, data.get("game_day", 0))
    if not result["success"]:
        return api_error(result["message"])
    db.commit()
    return api_success(result["message"], result)


@router.post("/court/bribe-judge")
def court_bribe_judge_endpoint(data: dict, db: Session = Depends(get_db)):
    """Phase G8: підкуп судді."""
    from backend.app.models import CourtCase
    from backend.app.services.court_service import bribe_judge

    case_uuid = try_uuid(data.get("case_id", ""))
    player_uuid = try_uuid(data.get("player_id", ""))
    if case_uuid is None or player_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    case = db.query(CourtCase).filter(CourtCase.id == case_uuid).first()
    player = db.query(Player).filter(Player.id == player_uuid).first()
    if not case or not player:
        return api_error("Не знайдено.")
    judge_number = int(data.get("judge_number", 0))
    amount = Decimal(str(data.get("amount", 0)))
    result = bribe_judge(db, case, player, judge_number, amount, data.get("game_day", 0))
    db.commit()
    return api_success(result["message"], result)


# --- Phase G8: Prison ---


@router.get("/prison/sentence")
def prison_sentence_endpoint(player_id: str, db: Session = Depends(get_db)):
    """Phase G8: статус ув'язнення гравця."""
    from backend.app.services.prison_service import get_active_sentence

    player_uuid = try_uuid(player_id)
    if player_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    sentence = get_active_sentence(db, player_uuid)
    if not sentence:
        return api_success("Активного ув'язнення немає.", {"sentence": None})
    return api_success(
        "Активне ув'язнення.",
        {
            "sentence": {
                "id": str(sentence.id),
                "days_total": sentence.days_total,
                "days_served": sentence.days_served,
                "days_remaining": sentence.days_remaining,
                "status": sentence.status,
                "business_impact": sentence.business_impact,
            }
        },
    )


@router.post("/prison/work")
def prison_work_endpoint(data: dict, db: Session = Depends(get_db)):
    """Phase G8: тюремна робота."""
    from backend.app.services.prison_service import get_active_sentence, prison_work

    player_uuid = try_uuid(data.get("player_id", ""))
    if player_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    player = db.query(Player).filter(Player.id == player_uuid).first()
    sentence = get_active_sentence(db, player_uuid)
    if not sentence or not player:
        return api_error("Ув'язнення не знайдено.")
    result = prison_work(db, sentence, player)
    db.commit()
    return api_success(result["message"], result)


@router.post("/prison/poker")
def prison_poker_endpoint(data: dict, db: Session = Depends(get_db)):
    """Phase G8: покер у тюрмі."""
    from backend.app.services.prison_service import get_active_sentence, prison_poker

    player_uuid = try_uuid(data.get("player_id", ""))
    if player_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    player = db.query(Player).filter(Player.id == player_uuid).first()
    sentence = get_active_sentence(db, player_uuid)
    if not sentence or not player:
        return api_error("Ув'язнення не знайдено.")
    bet = Decimal(str(data.get("bet", 0)))
    result = prison_poker(db, sentence, player, bet)
    db.commit()
    return api_success(result["message"], result)


@router.post("/prison/socialize")
def prison_socialize_endpoint(data: dict, db: Session = Depends(get_db)):
    """Phase G8: соціалізація з NPC-в'язнями."""
    from backend.app.services.prison_service import get_active_sentence, socialize

    player_uuid = try_uuid(data.get("player_id", ""))
    if player_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    player = db.query(Player).filter(Player.id == player_uuid).first()
    sentence = get_active_sentence(db, player_uuid)
    if not sentence or not player:
        return api_error("Ув'язнення не знайдено.")
    result = socialize(db, sentence, player)
    db.commit()
    return api_success(result["message"], result)


# --- Phase G8: Press ---


@router.post("/press/investigate")
def press_investigate_endpoint(data: dict, db: Session = Depends(get_db)):
    """Phase G8: почати розслідування."""
    from backend.app.services.press_service import start_investigation

    journalist_uuid = try_uuid(data.get("journalist_id", ""))
    target_uuid = try_uuid(data.get("target_id", ""))
    if journalist_uuid is None or target_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    journalist = db.query(Player).filter(Player.id == journalist_uuid).first()
    target = db.query(Player).filter(Player.id == target_uuid).first()
    if not journalist or not target:
        return api_error("Не знайдено.")
    incident_type = data.get("incident_type", "corruption")
    result = start_investigation(db, journalist, target, incident_type)
    if not result["success"]:
        return api_error(result["message"])
    db.commit()
    return api_success(result["message"], result)


@router.post("/press/publish")
def press_publish_endpoint(data: dict, db: Session = Depends(get_db)):
    """Phase G8: публікація статті."""
    from backend.app.models import PressInvestigation
    from backend.app.services.press_service import publish_article

    investigation_uuid = try_uuid(data.get("investigation_id", ""))
    target_uuid = try_uuid(data.get("target_id", ""))
    if investigation_uuid is None or target_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    investigation = db.query(PressInvestigation).filter(PressInvestigation.id == investigation_uuid).first()
    target = db.query(Player).filter(Player.id == target_uuid).first()
    if not investigation or not target:
        return api_error("Не знайдено.")
    result = publish_article(db, investigation, target, data.get("article_title"))
    if not result["success"]:
        return api_error(result["message"])
    db.commit()
    return api_success(result["message"], result)


@router.post("/press/blackmail")
def press_blackmail_endpoint(data: dict, db: Session = Depends(get_db)):
    """Phase G8: шантаж цільового гравця."""
    from backend.app.models import PressInvestigation
    from backend.app.services.press_service import offer_blackmail

    investigation_uuid = try_uuid(data.get("investigation_id", ""))
    journalist_uuid = try_uuid(data.get("journalist_id", ""))
    target_uuid = try_uuid(data.get("target_id", ""))
    if investigation_uuid is None or journalist_uuid is None or target_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    investigation = db.query(PressInvestigation).filter(PressInvestigation.id == investigation_uuid).first()
    journalist = db.query(Player).filter(Player.id == journalist_uuid).first()
    target = db.query(Player).filter(Player.id == target_uuid).first()
    if not investigation or not journalist or not target:
        return api_error("Не знайдено.")
    amount = Decimal(str(data.get("amount", 0)))
    result = offer_blackmail(db, investigation, journalist, target, amount)
    if not result["success"]:
        return api_error(result["message"])
    db.commit()
    return api_success(result["message"], result)


@router.post("/press/blackmail/{blackmail_id}/respond")
def press_blackmail_respond_endpoint(
    blackmail_id: str,
    data: dict,
    db: Session = Depends(get_db),
):
    """Phase G8: ціль відповідає на шантаж."""
    from backend.app.models import PressBlackmail, PressInvestigation
    from backend.app.services.press_service import respond_to_blackmail

    blackmail_uuid = try_uuid(blackmail_id)
    if blackmail_uuid is None:
        return api_error("Невірний ідентифікатор.")
    blackmail = db.query(PressBlackmail).filter(PressBlackmail.id == blackmail_uuid).first()
    if not blackmail:
        return api_error("Шантаж не знайдено.")
    target = db.query(Player).filter(Player.id == blackmail.target_id).first()
    journalist = db.query(Player).filter(Player.id == blackmail.journalist_id).first()
    investigation = (
        db.query(PressInvestigation).filter(PressInvestigation.id == blackmail.investigation_id).first()
        if blackmail.investigation_id
        else None
    )
    if not target or not journalist or not investigation:
        return api_error("Не знайдено.")
    action = data.get("action", "refuse")
    result = respond_to_blackmail(db, blackmail, target, journalist, investigation, action)
    if not result["success"]:
        return api_error(result["message"])
    db.commit()
    return api_success(result["message"], result)


# --- Phase G8: Lawyer ---


@router.post("/lawyer/engage")
def lawyer_engage_endpoint(data: dict, db: Session = Depends(get_db)):
    """Phase G8: найм адвоката для супроводу угоди."""
    from backend.app.services.lawyer_service import engage_lawyer

    lawyer_uuid = try_uuid(data.get("lawyer_id", ""))
    client_uuid = try_uuid(data.get("client_id", ""))
    if lawyer_uuid is None or client_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    lawyer = db.query(Player).filter(Player.id == lawyer_uuid).first()
    client = db.query(Player).filter(Player.id == client_uuid).first()
    if not lawyer or not client:
        return api_error("Не знайдено.")
    deal_type = data.get("deal_type", "general")
    amount = Decimal(str(data.get("amount", 0)))
    result = engage_lawyer(db, lawyer, client, deal_type, amount, data.get("game_day", 0))
    if not result["success"]:
        return api_error(result["message"])
    db.commit()
    return api_success(result["message"], result)


@router.post("/lawyer/appeal")
def lawyer_appeal_endpoint(data: dict, db: Session = Depends(get_db)):
    """Phase G8: адвокат допомагає з апеляцією."""
    from backend.app.models import CourtCase
    from backend.app.services.lawyer_service import appeal_with_lawyer

    case_uuid = try_uuid(data.get("case_id", ""))
    lawyer_uuid = try_uuid(data.get("lawyer_id", ""))
    client_uuid = try_uuid(data.get("client_id", ""))
    if case_uuid is None or lawyer_uuid is None or client_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    case = db.query(CourtCase).filter(CourtCase.id == case_uuid).first()
    lawyer = db.query(Player).filter(Player.id == lawyer_uuid).first()
    client = db.query(Player).filter(Player.id == client_uuid).first()
    if not case or not lawyer or not client:
        return api_error("Не знайдено.")
    result = appeal_with_lawyer(db, case, lawyer, client, data.get("game_day", 0))
    if not result["success"]:
        return api_error(result["message"])
    db.commit()
    return api_success(result["message"], result)


# --- Phase G6: Political System ---


@router.post("/city/offices/hire")
def hire_office_endpoint(
    data: dict,
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    db: Session = Depends(get_db),
):
    """Phase G6: найм гравця на посаду у мерію."""
    from backend.app.services.political_service import hire_office_worker

    city = db.query(City).first()
    if not city:
        return api_error("Місто не знайдене.")

    player_uuid = try_uuid(data.get("player_id", ""))
    if player_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    player = db.query(Player).filter(Player.id == player_uuid).first()
    if not player:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)

    position = data.get("position", "worker")
    department = data.get("department")
    game_day = data.get("game_day", 0)

    result = hire_office_worker(db, city, player, position, department, game_day)
    if not result["success"]:
        return api_error(result["message"])
    db.commit()
    return api_success(result["message"], result)


@router.get("/city/election")
def get_election_endpoint(db: Session = Depends(get_db)):
    """Phase G6: статус активних виборів мера."""
    from backend.app.services.political_service import (
        get_active_election,
        get_election_results,
    )

    city = db.query(City).first()
    if not city:
        return api_error("Місто не знайдене.")

    election = get_active_election(db, city.id)
    if not election:
        return api_success("Активних виборів немає.", {"election": None})

    results = get_election_results(db, election)
    return api_success(
        "Активні вибори мера.",
        {
            "election": {
                "id": str(election.id),
                "started_at_game_day": election.started_at_game_day,
                "ends_at_game_day": election.ends_at_game_day,
                "status": election.status,
            },
            "candidates": results,
        },
    )


@router.post("/city/election/start")
def start_election_endpoint(
    data: dict,
    db: Session = Depends(get_db),
):
    """Phase G6: почати вибори мера."""
    from backend.app.services.political_service import start_election

    city = db.query(City).first()
    if not city:
        return api_error("Місто не знайдене.")

    game_day = data.get("game_day", 0)
    result = start_election(db, city, game_day)
    if not result["success"]:
        return api_error(result["message"])
    db.commit()
    return api_success(result["message"], result)


@router.post("/city/election/register")
def register_candidate_endpoint(
    data: dict,
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    db: Session = Depends(get_db),
):
    """Phase G6: реєстрація кандидата у виборах."""
    from backend.app.services.political_service import get_active_election, register_candidate

    city = db.query(City).first()
    if not city:
        return api_error("Місто не знайдене.")

    election = get_active_election(db, city.id)
    if not election:
        return api_error("Немає активних виборів.")

    player_uuid = try_uuid(data.get("player_id", ""))
    if player_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    player = db.query(Player).filter(Player.id == player_uuid).first()
    if not player:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)

    platform = data.get("platform_text")
    game_day = data.get("game_day", 0)

    result = register_candidate(db, election, player, platform, game_day)
    if not result["success"]:
        return api_error(result["message"])
    db.commit()
    return api_success(result["message"], result)


@router.post("/city/election/vote")
def cast_vote_endpoint(
    data: dict,
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    db: Session = Depends(get_db),
):
    """Phase G6: гравець голосує за кандидата (відкрите голосування)."""
    from backend.app.models import ElectionCandidate
    from backend.app.services.political_service import cast_vote, get_active_election

    city = db.query(City).first()
    if not city:
        return api_error("Місто не знайдене.")

    election = get_active_election(db, city.id)
    if not election:
        return api_error("Немає активних виборів.")

    voter_uuid = try_uuid(data.get("voter_id", ""))
    if voter_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    voter = db.query(Player).filter(Player.id == voter_uuid).first()
    if not voter:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)

    candidate_uuid = try_uuid(data.get("candidate_id", ""))
    if candidate_uuid is None:
        return api_error("Невірний ідентифікатор кандидата.")
    candidate = db.query(ElectionCandidate).filter(ElectionCandidate.id == candidate_uuid).first()
    if not candidate:
        return api_error("Кандидат не знайдено.")

    game_day = data.get("game_day", 0)
    result = cast_vote(db, election, voter, candidate, game_day)
    if not result["success"]:
        return api_error(result["message"])
    db.commit()
    return api_success(result["message"], result)


@router.post("/city/election/conclude")
def conclude_election_endpoint(
    data: dict,
    db: Session = Depends(get_db),
):
    """Phase G6: підбити підсумки виборів."""
    from backend.app.services.political_service import conclude_election, get_active_election

    city = db.query(City).first()
    if not city:
        return api_error("Місто не знайдене.")

    election = get_active_election(db, city.id)
    if not election:
        return api_error("Немає активних виборів.")

    game_day = data.get("game_day", 0)
    result = conclude_election(db, election, game_day)
    if not result["success"]:
        return api_error(result["message"])
    db.commit()
    return api_success(result["message"], result)


@router.post("/city/election/bribe")
def offer_bribe_endpoint(
    data: dict,
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    db: Session = Depends(get_db),
):
    """Phase G6: підкуп голосів (тиньовий фонд)."""
    from backend.app.services.political_service import get_active_election, offer_bribe

    city = db.query(City).first()
    if not city:
        return api_error("Місто не знайдене.")

    election = get_active_election(db, city.id)
    if not election:
        return api_error("Немає активних виборів.")

    briber_uuid = try_uuid(data.get("briber_id", ""))
    if briber_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    briber = db.query(Player).filter(Player.id == briber_uuid).first()
    if not briber:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)

    voter_uuid = try_uuid(data.get("voter_id", ""))
    if voter_uuid is None:
        return api_error("Невірний ідентифікатор виборця.")
    voter = db.query(Player).filter(Player.id == voter_uuid).first()
    if not voter:
        return api_error("Виборець не знайдено.")

    amount = Decimal(str(data.get("amount", 0)))
    game_day = data.get("game_day", 0)

    result = offer_bribe(db, election, briber, voter, amount, game_day)
    if not result["success"]:
        return api_error(result["message"])
    db.commit()
    return api_success(result["message"], result)


@router.post("/city/election/bribe/{bribe_id}/respond")
def respond_bribe_endpoint(
    bribe_id: str,
    data: dict,
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    db: Session = Depends(get_db),
):
    """Phase G6: виборець відповідає на хабар."""
    from backend.app.models import VoteBribe
    from backend.app.services.political_service import respond_to_bribe

    bribe_uuid = try_uuid(bribe_id)
    if bribe_uuid is None:
        return api_error("Невірний ідентифікатор хабара.")
    bribe = db.query(VoteBribe).filter(VoteBribe.id == bribe_uuid).first()
    if not bribe:
        return api_error("Хабар не знайдено.")

    voter_uuid = try_uuid(data.get("voter_id", ""))
    if voter_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    voter = db.query(Player).filter(Player.id == voter_uuid).first()
    if not voter:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)

    accept = bool(data.get("accept", False))
    game_day = data.get("game_day", 0)

    result = respond_to_bribe(db, bribe, voter, accept, game_day)
    if not result["success"]:
        return api_error(result["message"])
    db.commit()
    return api_success(result["message"], result)


@router.post("/city/no-confidence")
def no_confidence_endpoint(
    data: dict,
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    db: Session = Depends(get_db),
):
    """Phase G6: вотум недовіри меру → дострокові вибори."""
    from backend.app.services.political_service import vote_of_no_confidence

    city = db.query(City).first()
    if not city:
        return api_error("Місто не знайдене.")

    player_uuid = try_uuid(data.get("player_id", ""))
    if player_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    player = db.query(Player).filter(Player.id == player_uuid).first()
    if not player:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)

    game_day = data.get("game_day", 0)
    result = vote_of_no_confidence(db, city, player, game_day)
    if not result["success"]:
        return api_error(result["message"])
    db.commit()
    return api_success(result["message"], result)


@router.post("/city/ai-mayor-invest")
def ai_mayor_invest_endpoint(
    data: dict,
    db: Session = Depends(get_db),
):
    """Phase G6: AI-мер інвестує з treasury у найгірший район."""
    from backend.app.services.political_service import ai_mayor_invest

    city = db.query(City).first()
    if not city:
        return api_error("Місто не знайдене.")

    game_day = data.get("game_day", 0)
    result = ai_mayor_invest(db, city, game_day)
    if not result["success"]:
        return api_error(result["message"])
    db.commit()
    return api_success(result["message"], result)


# --- Phase G5: Bank as Business ---


@router.post("/banks/{bank_id}/deposit")
def bank_deposit_endpoint(
    bank_id: str,
    data: dict,
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    db: Session = Depends(get_db),
):
    """Phase G5: гравець кладе депозит у банк."""
    from backend.app.services.bank_service import create_deposit

    bank_uuid = try_uuid(bank_id)
    if bank_uuid is None:
        return api_error("Невірний ідентифікатор банку.")
    bank = db.query(Business).filter(Business.id == bank_uuid).first()
    if not bank:
        return api_error("Банк не знайдено.")

    player_uuid = try_uuid(data.get("player_id", ""))
    if player_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    player = db.query(Player).filter(Player.id == player_uuid).first()
    if not player:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)

    amount = Decimal(str(data.get("amount", 0)))
    rate = data.get("interest_rate")
    interest_rate = Decimal(str(rate)) if rate is not None else None
    game_day = data.get("game_day", 0)

    result = create_deposit(db, bank, player, amount, interest_rate, game_day)
    if not result["success"]:
        return api_error(result["message"])
    db.commit()
    return api_success(result["message"], result)


@router.post("/banks/deposits/{deposit_id}/withdraw")
def bank_withdraw_endpoint(
    deposit_id: str,
    data: dict,
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    db: Session = Depends(get_db),
):
    """Phase G5: гравець знімає депозит."""
    from backend.app.models import BankDeposit
    from backend.app.services.bank_service import withdraw_deposit

    deposit_uuid = try_uuid(deposit_id)
    if deposit_uuid is None:
        return api_error("Невірний ідентифікатор депозиту.")
    deposit = db.query(BankDeposit).filter(BankDeposit.id == deposit_uuid).first()
    if not deposit:
        return api_error("Депозит не знайдено.")

    player_uuid = try_uuid(data.get("player_id", ""))
    if player_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    player = db.query(Player).filter(Player.id == player_uuid).first()
    if not player:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)

    result = withdraw_deposit(db, deposit, player)
    if not result["success"]:
        return api_error(result["message"])
    db.commit()
    return api_success(result["message"], result)


@router.post("/banks/{bank_id}/loan")
def bank_loan_endpoint(
    bank_id: str,
    data: dict,
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    db: Session = Depends(get_db),
):
    """Phase G5: гравець бере кредит у банку."""
    from backend.app.services.bank_service import issue_loan

    bank_uuid = try_uuid(bank_id)
    if bank_uuid is None:
        return api_error("Невірний ідентифікатор банку.")
    bank = db.query(Business).filter(Business.id == bank_uuid).first()
    if not bank:
        return api_error("Банк не знайдено.")

    player_uuid = try_uuid(data.get("player_id", ""))
    if player_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    player = db.query(Player).filter(Player.id == player_uuid).first()
    if not player:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)

    amount = Decimal(str(data.get("amount", 0)))
    rate = data.get("interest_rate")
    interest_rate = Decimal(str(rate)) if rate is not None else None
    term_days = int(data.get("term_days", 30))
    game_day = data.get("game_day", 0)

    result = issue_loan(db, bank, player, amount, interest_rate, term_days, game_day)
    if not result["success"]:
        return api_error(result["message"])
    db.commit()
    return api_success(result["message"], result)


@router.post("/banks/loans/{loan_id}/repay")
def bank_repay_endpoint(
    loan_id: str,
    data: dict,
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    db: Session = Depends(get_db),
):
    """Phase G5: гравець погашає кредит."""
    from backend.app.models import BankCredit
    from backend.app.services.bank_service import repay_loan

    loan_uuid = try_uuid(loan_id)
    if loan_uuid is None:
        return api_error("Невірний ідентифікатор кредиту.")
    loan = db.query(BankCredit).filter(BankCredit.id == loan_uuid).first()
    if not loan:
        return api_error("Кредит не знайдено.")

    player_uuid = try_uuid(data.get("player_id", ""))
    if player_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    player = db.query(Player).filter(Player.id == player_uuid).first()
    if not player:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)

    amount = Decimal(str(data.get("amount", 0)))
    result = repay_loan(db, loan, player, amount)
    if not result["success"]:
        return api_error(result["message"])
    db.commit()
    return api_success(result["message"], result)


@router.get("/auctions/active")
def list_active_auctions_endpoint(db: Session = Depends(get_db)):
    """Phase G5: список активних аукціонів банкрутів."""
    from backend.app.services.bank_service import list_active_auctions

    city = db.query(City).first()
    city_id = city.id if city else None
    auctions = list_active_auctions(db, city_id)
    return api_success(
        "Активні аукціони банкрутів.",
        {
            "auctions": [
                {
                    "id": str(a.id),
                    "business_id": str(a.business_id),
                    "starting_price": float(a.starting_price),
                    "highest_bid": float(a.highest_bid),
                    "ends_at": a.ends_at.isoformat(),
                    "status": a.status,
                }
                for a in auctions
            ]
        },
    )


@router.post("/auctions/{auction_id}/bid")
def auction_bid_endpoint(
    auction_id: str,
    data: dict,
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    db: Session = Depends(get_db),
):
    """Phase G5: гравець робить ставку на аукціоні банкрутів."""
    from backend.app.models import BankruptcyAuction
    from backend.app.services.bank_service import place_bid

    auction_uuid = try_uuid(auction_id)
    if auction_uuid is None:
        return api_error("Невірний ідентифікатор аукціону.")
    auction = db.query(BankruptcyAuction).filter(BankruptcyAuction.id == auction_uuid).first()
    if not auction:
        return api_error("Аукціон не знайдено.")

    player_uuid = try_uuid(data.get("player_id", ""))
    if player_uuid is None:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    player = db.query(Player).filter(Player.id == player_uuid).first()
    if not player:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)

    amount = Decimal(str(data.get("amount", 0)))
    result = place_bid(db, auction, player, amount)
    if not result["success"]:
        return api_error(result["message"])
    db.commit()
    return api_success(result["message"], result)


@router.post("/hostels/sleep/{player_id}")
def sleep_in_hostel(
    player_id: str,
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
):
    player = require_player(db, player_id, player_token)
    if not player:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    onboarding_error = require_completed_onboarding(db, player)
    if onboarding_error:
        return onboarding_error

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
    player = require_player(db, player_id, player_token)
    if not player:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    onboarding_error = require_completed_onboarding(db, player)
    if onboarding_error:
        return onboarding_error

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
        questions=[ExamQuestionData(id=q["id"], text=q["text"], options=q["options"]) for q in exam["questions"]],
    )
    return api_success("Інформація про іспит.", clean_exam.model_dump())


@router.post("/education/exam/submit")
def submit_exam(
    data: ExamAnswers,
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
):
    player = require_player(db, data.player_id, player_token)
    if not player:
        return api_error(INVALID_PLAYER_SESSION_MESSAGE)
    onboarding_error = require_completed_onboarding(db, player)
    if onboarding_error:
        return onboarding_error

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

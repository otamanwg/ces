from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models import BusinessBlueprint, LandParcel
from backend.app.repositories.business_blueprints import BusinessBlueprintRepository
from backend.app.services.money import money


@dataclass(frozen=True)
class StarterBusinessBlueprint:
    code: str
    name: str
    category: str
    business_type: str
    project_type: str
    description: str
    difficulty: str
    allowed_land_types: tuple[str, ...]
    allowed_zoning_types: tuple[str, ...]
    min_area_hectares: Decimal
    construction_cost: Decimal
    opening_fee: Decimal
    recommended_cash_reserve: Decimal
    daily_profit_min: Decimal
    daily_profit_max: Decimal
    upkeep_daily: Decimal
    risk_level: int
    risks: tuple[str, ...]
    metric_effects: dict[str, int]
    visual_archetype: str
    style_tags: tuple[str, ...]
    player_hints: tuple[str, ...]


STARTER_BUSINESS_BLUEPRINTS: tuple[StarterBusinessBlueprint, ...] = (
    StarterBusinessBlueprint(
        code="station_kiosk",
        name="Вокзальний кіоск",
        category="starter_retail",
        business_type="shop",
        project_type="commercial",
        description="Малий торговий кіоск біля автовокзалу для води, снеків і базових товарів.",
        difficulty="easy",
        allowed_land_types=("in_city",),
        allowed_zoning_types=("commercial",),
        min_area_hectares=Decimal("0.20"),
        construction_cost=Decimal("300.00"),
        opening_fee=Decimal("100.00"),
        recommended_cash_reserve=Decimal("150.00"),
        daily_profit_min=Decimal("20.00"),
        daily_profit_max=Decimal("55.00"),
        upkeep_daily=Decimal("8.00"),
        risk_level=1,
        risks=("Низька маржа.", "Залежність від пасажирського трафіку."),
        metric_effects={
            "expected_jobs": 2,
            "traffic_load": 3,
            "service_load": 2,
            "medical_load": 1,
            "public_benefit": 5,
        },
        visual_archetype="small_street_kiosk",
        style_tags=("compact", "street_retail", "starter"),
        player_hints=(
            "Підходить як перший бізнес після купівлі малої комерційної ділянки.",
            "Невеликий ризик, але прибуток теж обмежений.",
        ),
    ),
    StarterBusinessBlueprint(
        code="coffee_shop",
        name="Кав'ярня району",
        category="food_service",
        business_type="shop",
        project_type="commercial",
        description="Невелика кав'ярня для пасажирів, офісних працівників і мешканців центру.",
        difficulty="easy",
        allowed_land_types=("in_city",),
        allowed_zoning_types=("commercial",),
        min_area_hectares=Decimal("0.35"),
        construction_cost=Decimal("650.00"),
        opening_fee=Decimal("120.00"),
        recommended_cash_reserve=Decimal("300.00"),
        daily_profit_min=Decimal("30.00"),
        daily_profit_max=Decimal("85.00"),
        upkeep_daily=Decimal("15.00"),
        risk_level=2,
        risks=("Потрібні працівники.", "Вразлива до конкуренції у центрі."),
        metric_effects={
            "expected_jobs": 3,
            "traffic_load": 5,
            "service_load": 4,
            "medical_load": 1,
            "public_benefit": 8,
        },
        visual_archetype="corner_coffee_shop",
        style_tags=("food", "social", "starter"),
        player_hints=(
            "Краща за кіоск для району з робочими місцями і пішохідним трафіком.",
            "Залиште резерв на перші дні роботи, інакше upkeep швидко з'їсть касу.",
        ),
    ),
    StarterBusinessBlueprint(
        code="neighborhood_market",
        name="Міні-маркет",
        category="retail",
        business_type="shop",
        project_type="commercial",
        description="Малий продуктовий магазин для житлового або центрального району.",
        difficulty="medium",
        allowed_land_types=("in_city", "suburb"),
        allowed_zoning_types=("commercial", "residential"),
        min_area_hectares=Decimal("0.45"),
        construction_cost=Decimal("900.00"),
        opening_fee=Decimal("180.00"),
        recommended_cash_reserve=Decimal("500.00"),
        daily_profit_min=Decimal("45.00"),
        daily_profit_max=Decimal("125.00"),
        upkeep_daily=Decimal("25.00"),
        risk_level=3,
        risks=("Висока конкуренція.", "Потрібна стабільна логістика товарів."),
        metric_effects={
            "expected_jobs": 5,
            "traffic_load": 8,
            "service_load": 6,
            "medical_load": 2,
            "public_benefit": 12,
        },
        visual_archetype="neighborhood_market",
        style_tags=("retail", "daily_needs", "growth"),
        player_hints=(
            "Добрий вибір для району з житлом і стабільним потоком мешканців.",
            "Більше навантажує сервіси міста, тому AI-мер дивиться на районні метрики.",
        ),
    ),
    StarterBusinessBlueprint(
        code="repair_workshop",
        name="Ремонтна майстерня",
        category="services",
        business_type="factory",
        project_type="industrial",
        description="Майстерня з ремонту техніки, інструментів і малого транспорту.",
        difficulty="medium",
        allowed_land_types=("in_city", "near_city"),
        allowed_zoning_types=("industrial", "mixed"),
        min_area_hectares=Decimal("0.70"),
        construction_cost=Decimal("1200.00"),
        opening_fee=Decimal("150.00"),
        recommended_cash_reserve=Decimal("600.00"),
        daily_profit_min=Decimal("55.00"),
        daily_profit_max=Decimal("145.00"),
        upkeep_daily=Decimal("35.00"),
        risk_level=3,
        risks=("Шум і трафік.", "Потребує промислової або змішаної зони."),
        metric_effects={
            "expected_jobs": 4,
            "traffic_load": 10,
            "service_load": 8,
            "medical_load": 1,
            "public_benefit": 10,
        },
        visual_archetype="small_repair_workshop",
        style_tags=("industrial", "service", "utility"),
        player_hints=(
            "Не ставте майстерню у комфортному житловому районі без сильного плану.",
            "Підходить для промзони і майбутніх виробничих ланцюжків.",
        ),
    ),
    StarterBusinessBlueprint(
        code="private_hostel",
        name="Приватний хостел",
        category="housing",
        business_type="private_hostel",
        project_type="residential",
        description="Недороге житло для нових гравців і тимчасових мешканців міста.",
        difficulty="medium",
        allowed_land_types=("in_city", "suburb"),
        allowed_zoning_types=("residential",),
        min_area_hectares=Decimal("0.70"),
        construction_cost=Decimal("1400.00"),
        opening_fee=Decimal("160.00"),
        recommended_cash_reserve=Decimal("700.00"),
        daily_profit_min=Decimal("35.00"),
        daily_profit_max=Decimal("115.00"),
        upkeep_daily=Decimal("30.00"),
        risk_level=2,
        risks=(
            "Залежність від заселення.",
            "Потрібне медичне і сервісне покриття району.",
        ),
        metric_effects={
            "expected_jobs": 2,
            "traffic_load": 4,
            "service_load": 7,
            "medical_load": 4,
            "public_benefit": 18,
        },
        visual_archetype="budget_hostel_block",
        style_tags=("housing", "social", "starter_support"),
        player_hints=(
            "Це бізнес, який допомагає новим гравцям закріпитися в місті.",
            "Прибуток нижчий, але суспільна користь і стабільність вищі.",
        ),
    ),
    StarterBusinessBlueprint(
        code="pharmacy",
        name="Аптека",
        category="medical",
        business_type="shop",
        project_type="medical",
        description="Медичний роздріб, який підсилює район і знижує ризик побутових криз.",
        difficulty="medium",
        allowed_land_types=("in_city", "suburb"),
        allowed_zoning_types=("commercial", "residential"),
        min_area_hectares=Decimal("0.30"),
        construction_cost=Decimal("800.00"),
        opening_fee=Decimal("180.00"),
        recommended_cash_reserve=Decimal("450.00"),
        daily_profit_min=Decimal("35.00"),
        daily_profit_max=Decimal("100.00"),
        upkeep_daily=Decimal("22.00"),
        risk_level=2,
        risks=(
            "Потребує ліцензування в майбутній версії.",
            "Попит залежить від щільності району.",
        ),
        metric_effects={
            "expected_jobs": 3,
            "traffic_load": 4,
            "service_load": 3,
            "medical_load": 0,
            "public_benefit": 22,
        },
        visual_archetype="street_pharmacy",
        style_tags=("medical", "retail", "public_benefit"),
        player_hints=(
            "Аптека має помірний прибуток, зате добре вписується у районні метрики.",
            "Корисна там, де місту бракує медицини і AI-мер суворіший до навантаження.",
        ),
    ),
    StarterBusinessBlueprint(
        code="small_factory",
        name="Мала фабрика",
        category="manufacturing",
        business_type="factory",
        project_type="industrial",
        description="Невелике виробництво для промзони або зовнішнього розширення міста.",
        difficulty="hard",
        allowed_land_types=("in_city", "near_city"),
        allowed_zoning_types=("industrial", "mixed"),
        min_area_hectares=Decimal("1.20"),
        construction_cost=Decimal("2400.00"),
        opening_fee=Decimal("250.00"),
        recommended_cash_reserve=Decimal("1200.00"),
        daily_profit_min=Decimal("90.00"),
        daily_profit_max=Decimal("240.00"),
        upkeep_daily=Decimal("70.00"),
        risk_level=5,
        risks=(
            "Велике транспортне навантаження.",
            "Високий upkeep.",
            "AI-мер вимагатиме план сервісів.",
        ),
        metric_effects={
            "expected_jobs": 10,
            "traffic_load": 18,
            "service_load": 14,
            "medical_load": 3,
            "public_benefit": 16,
        },
        visual_archetype="small_factory_block",
        style_tags=("industrial", "jobs", "high_risk"),
        player_hints=(
            "Це не перший бізнес для стартового гравця: потрібна земля, резерв і терпіння.",
            "Потенційно прибуткова, але швидко створює міські проблеми без інфраструктури.",
        ),
    ),
    # --- Phase G3: Utility services ---
    StarterBusinessBlueprint(
        code="power_plant",
        name="Електростанція",
        category="utility",
        business_type="utility_power",
        project_type="industrial",
        description="Міська електростанція: забезпечує райони електроенергією. Комунальні платежі — основний дохід.",
        difficulty="hard",
        allowed_land_types=("in_city", "out_of_city"),
        allowed_zoning_types=("industrial",),
        min_area_hectares=Decimal("1.00"),
        construction_cost=Decimal("5000.00"),
        opening_fee=Decimal("500.00"),
        recommended_cash_reserve=Decimal("2000.00"),
        daily_profit_min=Decimal("50.00"),
        daily_profit_max=Decimal("120.00"),
        upkeep_daily=Decimal("30.00"),
        risk_level=3,
        risks=("Високі експлуатаційні витрати.", "Банкрутство → контракт з сусіднім містом за завищеними цінами."),
        metric_effects={
            "expected_jobs": 5,
            "traffic_load": 8,
            "service_load": 0,
            "medical_load": 0,
            "public_benefit": 30,
        },
        visual_archetype="power_plant",
        style_tags=("industrial", "utility", "critical_infrastructure"),
        player_hints=(
            "Критична інфраструктура: без електрики місто живе 1 день, потім екстрений контракт.",
            "Дохід від комунальних платежів усіх бізнесів міста.",
        ),
    ),
    StarterBusinessBlueprint(
        code="water_works",
        name="Водоканал",
        category="utility",
        business_type="utility_water",
        project_type="industrial",
        description="Міський водоканал: забезпечує райони водопостачанням і водовідведенням.",
        difficulty="hard",
        allowed_land_types=("in_city", "out_of_city"),
        allowed_zoning_types=("industrial",),
        min_area_hectares=Decimal("0.80"),
        construction_cost=Decimal("3500.00"),
        opening_fee=Decimal("350.00"),
        recommended_cash_reserve=Decimal("1500.00"),
        daily_profit_min=Decimal("40.00"),
        daily_profit_max=Decimal("90.00"),
        upkeep_daily=Decimal("20.00"),
        risk_level=3,
        risks=("Високі експлуатаційні витрати.", "Банкрутство → екстрений контракт."),
        metric_effects={
            "expected_jobs": 4,
            "traffic_load": 5,
            "service_load": 0,
            "medical_load": 0,
            "public_benefit": 25,
        },
        visual_archetype="water_works",
        style_tags=("industrial", "utility", "critical_infrastructure"),
        player_hints=(
            "Критична інфраструктура: без води райони швидко деградують.",
            "Дохід від комунальних платежів.",
        ),
    ),
    StarterBusinessBlueprint(
        code="waste_plant",
        name="Сміттєпереробний завод",
        category="utility",
        business_type="utility_waste",
        project_type="industrial",
        description="Завод переробки відходів: утримує waste_management районів. Без нього сміття накопичується.",
        difficulty="hard",
        allowed_land_types=("in_city", "out_of_city"),
        allowed_zoning_types=("industrial",),
        min_area_hectares=Decimal("0.60"),
        construction_cost=Decimal("2500.00"),
        opening_fee=Decimal("250.00"),
        recommended_cash_reserve=Decimal("1000.00"),
        daily_profit_min=Decimal("30.00"),
        daily_profit_max=Decimal("70.00"),
        upkeep_daily=Decimal("15.00"),
        risk_level=2,
        risks=("Банкрутство → сміття накопичується, happiness падає.", "Екстрений контракт з сусіднім містом."),
        metric_effects={
            "expected_jobs": 3,
            "traffic_load": 6,
            "service_load": 0,
            "medical_load": 0,
            "public_benefit": 20,
        },
        visual_archetype="waste_plant",
        style_tags=("industrial", "utility", "sanitation"),
        player_hints=(
            "Без сміттєзаводу waste_management падає, happiness знижується.",
            "Дохід від комунальних платежів.",
        ),
    ),
    # --- Phase G5: Bank ---
    StarterBusinessBlueprint(
        code="bank",
        name="Банк",
        category="finance",
        business_type="bank",
        project_type="commercial",
        description="Банк: приймає депозити, видає кредити, оперує з власного cash_balance.",
        difficulty="hard",
        allowed_land_types=("in_city",),
        allowed_zoning_types=("commercial",),
        min_area_hectares=Decimal("0.30"),
        construction_cost=Decimal("8000.00"),
        opening_fee=Decimal("800.00"),
        recommended_cash_reserve=Decimal("20000.00"),
        daily_profit_min=Decimal("20.00"),
        daily_profit_max=Decimal("80.00"),
        upkeep_daily=Decimal("25.00"),
        risk_level=4,
        risks=(
            "Банк-рун: якщо вкладники знімають одночасно — банкрот.",
            "Дефолт позичальників → втрата principal.",
            "Відмова у кредитах при високому criminal_rep (Phase H).",
        ),
        metric_effects={
            "expected_jobs": 3,
            "traffic_load": 10,
            "service_load": 0,
            "medical_load": 0,
            "public_benefit": 15,
        },
        visual_archetype="bank",
        style_tags=("commercial", "finance", "high_value"),
        player_hints=(
            "Банк оперує з власного cash_balance — потрібен великий резерв.",
            "Дохід: різниця між ставкою за кредитами і ставкою за депозитами.",
            "Банкрутство бізнесу → аукціон (24 години реального часу).",
        ),
    ),
    # --- Phase G9: Casino ---
    StarterBusinessBlueprint(
        code="casino",
        name="Казино",
        category="gambling",
        business_type="casino",
        project_type="commercial",
        description="Казино: блекджек, рулетка, покер. Дохід з rake та house edge. Ліцензія від мера, податок 25%.",
        difficulty="hard",
        allowed_land_types=("in_city",),
        allowed_zoning_types=("commercial",),
        min_area_hectares=Decimal("0.40"),
        construction_cost=Decimal("15000.00"),
        opening_fee=Decimal("1500.00"),
        recommended_cash_reserve=Decimal("30000.00"),
        daily_profit_min=Decimal("30.00"),
        daily_profit_max=Decimal("120.00"),
        upkeep_daily=Decimal("40.00"),
        risk_level=5,
        risks=(
            "Ліцензія може бути відкликана мером.",
            "Перевірка поліції (підозра на відмивання).",
            "Преса — скандал при зв'язках з криміналом.",
        ),
        metric_effects={
            "expected_jobs": 5,
            "traffic_load": 20,
            "service_load": 0,
            "medical_load": 0,
            "public_benefit": 5,
        },
        visual_archetype="casino",
        style_tags=("commercial", "entertainment", "high_value"),
        player_hints=(
            "Дохід: rake (5-10% з покеру) + house edge (блекджек ~1-2%, рулетка ~5%).",
            "Податок 25% на дохід (вищий за звичайний бізнес).",
            "Ліцензійний збір щомісяця йде мерії.",
        ),
    ),
    # --- Phase G9: Atelier ---
    StarterBusinessBlueprint(
        code="atelier",
        name="Ательє",
        category="fashion",
        business_type="atelier",
        project_type="commercial",
        description="Ательє: створення скінів (JSON-конфіг), продаж (унікальні/масові), аукціон скінів.",
        difficulty="medium",
        allowed_land_types=("in_city",),
        allowed_zoning_types=("commercial",),
        min_area_hectares=Decimal("0.20"),
        construction_cost=Decimal("6000.00"),
        opening_fee=Decimal("600.00"),
        recommended_cash_reserve=Decimal("8000.00"),
        daily_profit_min=Decimal("15.00"),
        daily_profit_max=Decimal("60.00"),
        upkeep_daily=Decimal("15.00"),
        risk_level=2,
        risks=(
            "Мода змінюється — попит на скіни коливається.",
            "Конкуренція з іншими ательє.",
        ),
        metric_effects={
            "expected_jobs": 2,
            "traffic_load": 5,
            "service_load": 0,
            "medical_load": 0,
            "public_benefit": 10,
        },
        visual_archetype="atelier",
        style_tags=("commercial", "fashion", "creative"),
        player_hints=(
            "Скін — JSON-конфіг (зачіска, кольори, костюм).",
            "Унікальні скіни — дорогі, статусні. Масові — дешеві, доступні.",
            "Репутація дизайнера росте від популярних скінів.",
        ),
    ),
    # --- Phase G8: Media Outlet (Press) ---
    StarterBusinessBlueprint(
        code="media_outlet",
        name="Медіа-контора",
        category="media",
        business_type="media_outlet",
        project_type="commercial",
        description="Преса: журналісти, розслідування, публікація, реклама, шантаж (тіньова механіка).",
        difficulty="medium",
        allowed_land_types=("in_city",),
        allowed_zoning_types=("commercial",),
        min_area_hectares=Decimal("0.15"),
        construction_cost=Decimal("4000.00"),
        opening_fee=Decimal("400.00"),
        recommended_cash_reserve=Decimal("5000.00"),
        daily_profit_min=Decimal("10.00"),
        daily_profit_max=Decimal("50.00"),
        upkeep_daily=Decimal("10.00"),
        risk_level=3,
        risks=(
            "Шантаж — злочин (повідомлення в поліцію → corruption_log).",
            "Сенсаційні статті → скандали, політичні наслідки.",
        ),
        metric_effects={
            "expected_jobs": 2,
            "traffic_load": 5,
            "service_load": 0,
            "medical_load": 0,
            "public_benefit": 10,
        },
        visual_archetype="media",
        style_tags=("commercial", "media", "creative"),
        player_hints=(
            "Дохід: реклама + підписки + шантаж (тіньова).",
            "Розслідування накопичує press_evidence → публікація або шантаж.",
            "Шантаж НЕ впливає на репутацію журналіста.",
        ),
    ),
)


STARTER_BLUEPRINT_COUNT = len(STARTER_BUSINESS_BLUEPRINTS)


def ensure_business_blueprints(db: Session) -> None:
    blueprint_repo = BusinessBlueprintRepository(db)

    for starter in STARTER_BUSINESS_BLUEPRINTS:
        data = _starter_to_model_data(starter)
        existing = blueprint_repo.get_by_code(starter.code)
        if existing:
            for key, value in data.items():
                setattr(existing, key, value)
        else:
            db.add(BusinessBlueprint(**data))


def get_active_business_blueprints(db: Session) -> list[BusinessBlueprint]:
    return BusinessBlueprintRepository(db).get_all_active()


def get_business_blueprint(db: Session, blueprint_id: UUID) -> BusinessBlueprint | None:
    blueprint = BusinessBlueprintRepository(db).get_by_id(blueprint_id)
    if blueprint and blueprint.is_active:
        return blueprint
    return None


def validate_blueprint_for_parcel(blueprint: BusinessBlueprint, parcel: LandParcel) -> str | None:
    allowed_land_types = blueprint.allowed_land_types or []
    if allowed_land_types and parcel.land_type not in allowed_land_types:
        return "Цей бізнес не підходить для типу землі обраної ділянки."

    allowed_zoning_types = blueprint.allowed_zoning_types or []
    if allowed_zoning_types and parcel.zoning_type not in allowed_zoning_types:
        return "Цей бізнес не підходить для зонування обраної ділянки."

    if Decimal(str(parcel.area_hectares)) < Decimal(str(blueprint.min_area_hectares)):
        return f"Для цього бізнесу потрібна ділянка від {money(blueprint.min_area_hectares):.2f} га."

    return None


def blueprint_metric(blueprint: BusinessBlueprint, key: str, fallback: int = 0) -> int:
    value = (blueprint.metric_effects or {}).get(key, fallback)
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return max(0, fallback)


def _starter_to_model_data(starter: StarterBusinessBlueprint) -> dict:
    return {
        "code": starter.code,
        "name": starter.name,
        "category": starter.category,
        "business_type": starter.business_type,
        "project_type": starter.project_type,
        "description": starter.description,
        "difficulty": starter.difficulty,
        "allowed_land_types": list(starter.allowed_land_types),
        "allowed_zoning_types": list(starter.allowed_zoning_types),
        "min_area_hectares": starter.min_area_hectares,
        "construction_cost": starter.construction_cost,
        "opening_fee": starter.opening_fee,
        "recommended_cash_reserve": starter.recommended_cash_reserve,
        "daily_profit_min": starter.daily_profit_min,
        "daily_profit_max": starter.daily_profit_max,
        "upkeep_daily": starter.upkeep_daily,
        "risk_level": starter.risk_level,
        "risks": list(starter.risks),
        "metric_effects": dict(starter.metric_effects),
        "visual_archetype": starter.visual_archetype,
        "style_tags": list(starter.style_tags),
        "player_hints": list(starter.player_hints),
        "is_active": True,
    }

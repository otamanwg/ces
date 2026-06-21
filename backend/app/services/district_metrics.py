"""
Динамічні метрики районів (Phase G1).

Перераховує всі метрики району на day tick на основі:
- кількості та типу бізнесів у районі
- населення (гравці + NPC)
- інфраструктурних потужностей (поки базові, без комунальних служб — Phase G3)
- сезонних множників (season_service)
- feedback loops між метриками (div. GAMEPLAY_CORE_MODEL.md §20)

Зберігає snapshot у DistrictMetricSnapshot для історії та трендів.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.models import (
    Building,
    Business,
    CityDistrict,
    DistrictMetricSnapshot,
    NpcResident,
)
from backend.app.services.season_service import SeasonModifiers, get_season_modifiers

logger = logging.getLogger("DistrictMetrics")

CLAMP_MIN = 0.0
CLAMP_MAX = 100.0

# Категоризація типів бізнесів для формул метрик.
# У Phase G3 ці категорії будуть доповнені комунальними службами.
PRODUCTION_BUSINESS_TYPES = frozenset({"factory", "utility_water", "utility_housing"})
COMMERCE_BUSINESS_TYPES = frozenset({"shop", "private_hostel"})
UTILITY_BUSINESS_TYPES = frozenset({"utility_water", "utility_housing"})


@dataclass
class DistrictBusinessCounts:
    active_total: int = 0
    production: int = 0
    commerce: int = 0
    utility: int = 0


@dataclass
class CompositeIndices:
    economy_score: float
    production_score: float
    household_score: float
    commerce_score: float
    infrastructure_score: float
    social_score: float


def _clamp(value: float, lo: float = CLAMP_MIN, hi: float = CLAMP_MAX) -> float:
    return max(lo, min(hi, value))


def _weighted_avg(*pairs: tuple[float, float]) -> float:
    """pairs = (value, weight). Повертає зважене середнє, зведене до [0,100]."""
    total_weight = sum(w for _, w in pairs)
    if total_weight <= 0:
        return 50.0
    return _clamp(sum(v * w for v, w in pairs) / total_weight)


def _count_businesses_by_district(db: Session, district_id: uuid.UUID) -> DistrictBusinessCounts:
    # Business не має прямого district_id; пов'язано через Building.business_id.
    rows = (
        db.query(Business.type, func.count(Business.id))
        .join(Building, Building.business_id == Business.id)
        .filter(Building.district_id == district_id, Business.status == "active")
        .group_by(Business.type)
        .all()
    )
    counts = DistrictBusinessCounts()
    for b_type, cnt in rows:
        counts.active_total += int(cnt)
        if b_type in PRODUCTION_BUSINESS_TYPES:
            counts.production += int(cnt)
        if b_type in COMMERCE_BUSINESS_TYPES:
            counts.commerce += int(cnt)
        if b_type in UTILITY_BUSINESS_TYPES:
            counts.utility += int(cnt)
    return counts


def _district_population(db: Session, district_id: uuid.UUID) -> tuple[int, int]:
    """Повертає (player_count, npc_count) у районі.

    Player не має прямого district_id у поточній схемі (Phase G1).
    Населення району поки оцінюється через NPC (Phase G2) + district.population
    (яку AI-мер може встановлювати). player_count повертає 0 до Phase G2.
    """
    npc_count = (
        db.query(func.count(NpcResident.id))
        .filter(NpcResident.district_id == district_id)
        .scalar()
        or 0
    )
    return 0, npc_count


def _latest_snapshot(db: Session, district_id: uuid.UUID) -> DistrictMetricSnapshot | None:
    return (
        db.query(DistrictMetricSnapshot)
        .filter(DistrictMetricSnapshot.district_id == district_id)
        .order_by(DistrictMetricSnapshot.game_day.desc())
        .first()
    )


def recalculate_district_metrics(
    db: Session,
    district: CityDistrict,
    game_day: int,
    season_modifiers: SeasonModifiers | None = None,
) -> DistrictMetricSnapshot:
    """Перераховує всі метрики району і зберігає snapshot.

    Повертає створений DistrictMetricSnapshot. Не комітить — викликець відповідає
    за транзакцію (щоб можна було об'єднати з іншими day-tick операціями).
    """
    if season_modifiers is None:
        season_modifiers = get_season_modifiers(game_day)

    counts = _count_businesses_by_district(db, district.id)
    _player_count, npc_count = _district_population(db, district.id)
    population = float(npc_count) + float(district.population)

    # --- Базові "потужності" інфраструктури ---
    # У Phase G1 комунальних служб ще немає як окремих бізнесів з потужністю,
    # тому використовуємо базові 100 і знижуємо попитом. Phase G3 замінить це
    # на реальні потужності електростанцій/водоканалів.
    power_capacity = 100.0
    water_capacity = 100.0

    # --- Сезонні дельти ---
    sm = season_modifiers

    # --- Сирі метрики ---
    # pollution: виробництво + трафік - озеленення - дощова вода (water>80) + сезон
    pollution = _clamp(
        20.0
        + counts.production * 8.0
        + float(district.traffic) * 0.3
        - float(district.green_space) * 3.0
        - (5.0 if float(district.water_supply) > 80.0 else 0.0)
        + sm.pollution_delta
    )

    # power_supply: потужність - попит населення - попит бізнесів - сезонний попит
    power_supply = _clamp(
        power_capacity
        - population * 0.5
        - counts.active_total * 2.0
        - sm.power_demand_delta
    )

    # water_supply: потужність - попит населення - попит бізнесів - сезонний попит
    water_supply = _clamp(
        water_capacity
        - population * 0.4
        - counts.active_total * 1.5
        - sm.water_demand_delta
    )

    # waste_management: базова - попит населення + озеленення (компост)
    waste_management = _clamp(
        70.0
        - population * 0.3
        + float(district.green_space) * 0.5
    )

    # fire_safety: базова + інфраструктура - виробництво (ризик пожежі)
    fire_safety = _clamp(
        60.0
        + float(district.service_coverage) * 0.2
        - counts.production * 3.0
    )

    # education_coverage: базова + сезон (осінь = шкільний сезон)
    education_coverage = _clamp(
        float(district.education_coverage) + sm.education_coverage_delta * 0.1
    )

    # green_space: стабільна (змінюється AI-мером або гравцями пізніше)
    green_space = _clamp(float(district.green_space))

    # housing_capacity: базова + utility_housing бізнеси
    housing_capacity = _clamp(
        40.0 + counts.utility * 15.0 + float(district.green_space) * 0.1
    )

    # happiness: базова + desirability + (100-crime) + (100-pollution) + job_supply - rent + сезон
    happiness = _clamp(
        30.0
        + float(district.desirability) * 0.2
        + (100.0 - float(district.crime_risk)) * 0.15
        + (100.0 - pollution) * 0.1
        + float(district.job_supply) * 0.1
        - (10.0 if float(district.rent_level) > 80.0 else 0.0)
        + sm.happiness_delta
    )

    # crime_risk: базова + (100-happiness)*0.3 + (100-service_coverage)*0.4 - education*0.2 + сезон
    crime_risk = _clamp(
        20.0
        + (100.0 - happiness) * 0.3
        + (100.0 - float(district.service_coverage)) * 0.4
        - education_coverage * 0.2
        + sm.crime_risk_delta
    )

    # desirability: базова + green + (100-pollution) + (100-crime) + education + medical - traffic + сезон
    desirability = _clamp(
        20.0
        + green_space * 0.3
        + (100.0 - pollution) * 0.2
        + (100.0 - crime_risk) * 0.2
        + education_coverage * 0.1
        + float(district.medical_coverage) * 0.1
        - (15.0 if float(district.traffic) > 70.0 else 0.0)
        + sm.desirability_delta
    )

    # land_value: базова + desirability*0.4 + (100-pollution)*0.1 + infrastructure*0.2 - crime + сезон
    # infrastructure_score обчислюється нижче, тому використовуємо proxy
    infra_proxy = _weighted_avg(
        (power_supply, 0.25),
        (water_supply, 0.25),
        (waste_management, 0.2),
        (fire_safety, 0.15),
        (100.0 - float(district.traffic), 0.15),
    )
    land_value = _clamp(
        30.0
        + desirability * 0.4
        + (100.0 - pollution) * 0.1
        + infra_proxy * 0.2
        - (20.0 if crime_risk > 70.0 else 0.0)
        + sm.land_value_delta
    )

    # traffic: базова + бізнеси + населення + сезон
    traffic = _clamp(
        float(district.traffic)
        + counts.active_total * 2.0
        + population * 0.2
        + sm.traffic_delta
    )

    # job_supply: базова + commerce + сезон (весняний/літній бум)
    job_supply = _clamp(
        float(district.job_supply)
        + counts.commerce * 5.0
        + sm.job_supply_commerce_delta
    )

    # --- Оновлюємо поля району (in-place) ---
    district.pollution = pollution
    district.power_supply = power_supply
    district.water_supply = water_supply
    district.waste_management = waste_management
    district.fire_safety = fire_safety
    district.education_coverage = education_coverage
    district.green_space = green_space
    district.housing_capacity = housing_capacity
    district.happiness = happiness
    district.crime_risk = int(round(crime_risk))
    district.desirability = int(round(desirability))
    district.land_value = int(round(land_value))
    district.traffic = int(round(traffic))
    district.job_supply = int(round(job_supply))
    district.population = population

    # --- Композитні індекси (0-100) ---
    composite = CompositeIndices(
        economy_score=_weighted_avg(
            (_normalize_count(counts.active_total, 20), 0.3),
            (job_supply, 0.3),
            (float(district.land_value), 0.2),
            (happiness, 0.2),
        ),
        production_score=_weighted_avg(
            (_normalize_count(counts.production, 10), 0.4),
            (power_supply, 0.3),
            (100.0 - pollution, 0.3),
        ),
        household_score=_weighted_avg(
            (housing_capacity, 0.3),
            (_normalize_count(int(population), 50), 0.2),
            (100.0 - float(district.rent_level), 0.2),
            (green_space, 0.3),
        ),
        commerce_score=_weighted_avg(
            (_normalize_count(counts.commerce, 15), 0.4),
            (job_supply, 0.3),
            (desirability, 0.3),
        ),
        infrastructure_score=infra_proxy,
        social_score=_weighted_avg(
            (education_coverage, 0.3),
            (float(district.medical_coverage), 0.3),
            (happiness, 0.2),
            (100.0 - crime_risk, 0.2),
        ),
    )

    # --- Snapshot ---
    snapshot = DistrictMetricSnapshot(
        district_id=district.id,
        game_day=game_day,
        rent_level=float(district.rent_level),
        job_supply=job_supply,
        crime_risk=crime_risk,
        traffic=traffic,
        service_coverage=float(district.service_coverage),
        medical_coverage=float(district.medical_coverage),
        land_value=land_value,
        desirability=desirability,
        pollution=pollution,
        education_coverage=education_coverage,
        fire_safety=fire_safety,
        power_supply=power_supply,
        water_supply=water_supply,
        waste_management=waste_management,
        population=population,
        housing_capacity=housing_capacity,
        green_space=green_space,
        happiness=happiness,
        economy_score=composite.economy_score,
        production_score=composite.production_score,
        household_score=composite.household_score,
        commerce_score=composite.commerce_score,
        infrastructure_score=composite.infrastructure_score,
        social_score=composite.social_score,
        season=sm.season,
    )
    db.add(snapshot)
    return snapshot


def recalculate_all_districts(db: Session, city_id: uuid.UUID, game_day: int) -> list[DistrictMetricSnapshot]:
    """Перераховує всі райони міста на day tick. Повертає список snapshot-ів."""
    districts = db.query(CityDistrict).filter(CityDistrict.city_id == city_id).all()
    snapshots: list[DistrictMetricSnapshot] = []
    season_modifiers = get_season_modifiers(game_day)
    for district in districts:
        snapshot = recalculate_district_metrics(db, district, game_day, season_modifiers)
        snapshots.append(snapshot)
    return snapshots


def get_radar_with_trend(db: Session, district_id: uuid.UUID, trend_days: int = 7) -> dict:
    """Повертає 6 композитних індексів + тренд за останні N днів.

    Формат: {
        "indices": {"economy_score": float, ...},
        "trend": {"economy_score": float, ...},  # delta = current - N_days_ago
        "season": str,
        "game_day": int,
    }
    """
    latest = _latest_snapshot(db, district_id)
    if latest is None:
        return {
            "indices": {
                "economy_score": 50.0,
                "production_score": 50.0,
                "household_score": 50.0,
                "commerce_score": 50.0,
                "infrastructure_score": 50.0,
                "social_score": 50.0,
            },
            "trend": {
                "economy_score": 0.0,
                "production_score": 0.0,
                "household_score": 0.0,
                "commerce_score": 0.0,
                "infrastructure_score": 0.0,
                "social_score": 0.0,
            },
            "season": "spring",
            "game_day": 0,
        }

    indices = {
        "economy_score": latest.economy_score,
        "production_score": latest.production_score,
        "household_score": latest.household_score,
        "commerce_score": latest.commerce_score,
        "infrastructure_score": latest.infrastructure_score,
        "social_score": latest.social_score,
    }

    # Тренд: різниця між поточним і snapshot N днів тому
    target_day = max(0, latest.game_day - trend_days)
    past = (
        db.query(DistrictMetricSnapshot)
        .filter(
            DistrictMetricSnapshot.district_id == district_id,
            DistrictMetricSnapshot.game_day <= target_day,
        )
        .order_by(DistrictMetricSnapshot.game_day.desc())
        .first()
    )
    if past is None:
        trend = dict.fromkeys(indices, 0.0)
    else:
        trend = {
            "economy_score": latest.economy_score - past.economy_score,
            "production_score": latest.production_score - past.production_score,
            "household_score": latest.household_score - past.household_score,
            "commerce_score": latest.commerce_score - past.commerce_score,
            "infrastructure_score": latest.infrastructure_score - past.infrastructure_score,
            "social_score": latest.social_score - past.social_score,
        }

    return {
        "indices": indices,
        "trend": trend,
        "season": latest.season,
        "game_day": latest.game_day,
    }


def _normalize_count(count: int, benchmark: int) -> float:
    """Нормалізує кількість до 0-100 (count/benchmark * 100, з clamp)."""
    if benchmark <= 0:
        return 50.0
    return _clamp((count / benchmark) * 100.0)

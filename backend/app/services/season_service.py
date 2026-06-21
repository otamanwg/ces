"""
Сезонна модель для динамічних метрик районів (Phase G1).

3-4 реальні години = 1 ігровий день. ~90 ігрових днів = 1 сезон.
Стартовий сезон — весна (найсприятливіший для нового міста).

Множники — константи для першої версії (див. GAMEPLAY_CORE_MODEL.md §20).
Плавний перехід між сезонами — 7 днів градієнт.
"""

from __future__ import annotations

from dataclasses import dataclass

DAYS_PER_SEASON = 90
SEASON_TRANSITION_DAYS = 7
START_SEASON_INDEX = 0  # 0=spring, 1=summer, 2=autumn, 3=winter

_SEASON_ORDER = ("spring", "summer", "autumn", "winter")


@dataclass(frozen=True)
class SeasonModifiers:
    """Множники/дельти, що застосовуються до сирих метрик на day tick."""

    season: str
    desirability_delta: float
    power_demand_delta: float  # додається до попиту (зменшує power_supply)
    job_supply_commerce_delta: float
    pollution_delta: float
    crime_risk_delta: float
    land_value_delta: float
    water_demand_delta: float
    traffic_delta: float
    education_coverage_delta: float
    happiness_delta: float


_SEASON_MODIFIERS: dict[str, SeasonModifiers] = {
    "spring": SeasonModifiers(
        season="spring",
        desirability_delta=15.0,
        power_demand_delta=-10.0,
        job_supply_commerce_delta=10.0,
        pollution_delta=-5.0,
        crime_risk_delta=-5.0,
        land_value_delta=5.0,
        water_demand_delta=0.0,
        traffic_delta=0.0,
        education_coverage_delta=0.0,
        happiness_delta=5.0,
    ),
    "summer": SeasonModifiers(
        season="summer",
        desirability_delta=5.0,
        power_demand_delta=20.0,
        job_supply_commerce_delta=15.0,
        pollution_delta=10.0,
        crime_risk_delta=5.0,
        land_value_delta=0.0,
        water_demand_delta=15.0,
        traffic_delta=0.0,
        education_coverage_delta=0.0,
        happiness_delta=0.0,
    ),
    "autumn": SeasonModifiers(
        season="autumn",
        desirability_delta=-5.0,
        power_demand_delta=5.0,
        job_supply_commerce_delta=-10.0,
        pollution_delta=15.0,
        crime_risk_delta=0.0,
        land_value_delta=-5.0,
        water_demand_delta=0.0,
        traffic_delta=0.0,
        education_coverage_delta=10.0,
        happiness_delta=-5.0,
    ),
    "winter": SeasonModifiers(
        season="winter",
        desirability_delta=-15.0,
        power_demand_delta=40.0,
        job_supply_commerce_delta=-15.0,
        pollution_delta=25.0,
        crime_risk_delta=10.0,
        land_value_delta=0.0,
        water_demand_delta=-10.0,
        traffic_delta=-10.0,
        education_coverage_delta=0.0,
        happiness_delta=-10.0,
    ),
}


def season_for_game_day(game_day: int) -> str:
    """Повертає назву сезону для заданого ігрового дня.

    game_day=0 — старт (весна). Кожен сезон триває DAYS_PER_SEASON днів.
    """
    if game_day < 0:
        game_day = 0
    season_index = ((game_day // DAYS_PER_SEASON) + START_SEASON_INDEX) % len(_SEASON_ORDER)
    return _SEASON_ORDER[season_index]


def season_transition_factor(game_day: int) -> float:
    """Фактор плавного переходу між сезонами (0..1).

    0 — повністю поточний сезон, 1 — повністю наступний.
    Останні SEASON_TRANSITION_DAYS сезону — плавний градієнт до наступного.
    """
    day_in_season = game_day % DAYS_PER_SEASON
    transition_start = DAYS_PER_SEASON - SEASON_TRANSITION_DAYS
    if day_in_season < transition_start:
        return 0.0
    return (day_in_season - transition_start) / SEASON_TRANSITION_DAYS


def get_season_modifiers(game_day: int) -> SeasonModifiers:
    """Повертає інтерпольовані модифікатори для заданого ігрового дня.

    Під час останніх 7 днів сезону лінійно інтерполює між поточним і наступним
    сезоном, щоб перехід був плавним.
    """
    current = season_for_game_day(game_day)
    factor = season_transition_factor(game_day)
    if factor <= 0.0:
        return _SEASON_MODIFIERS[current]
    next_day = game_day + 1
    next_season = season_for_game_day(next_day)
    if next_season == current:
        return _SEASON_MODIFIERS[current]
    cur = _SEASON_MODIFIERS[current]
    nxt = _SEASON_MODIFIERS[next_season]
    return SeasonModifiers(
        season=current,
        desirability_delta=_lerp(cur.desirability_delta, nxt.desirability_delta, factor),
        power_demand_delta=_lerp(cur.power_demand_delta, nxt.power_demand_delta, factor),
        job_supply_commerce_delta=_lerp(cur.job_supply_commerce_delta, nxt.job_supply_commerce_delta, factor),
        pollution_delta=_lerp(cur.pollution_delta, nxt.pollution_delta, factor),
        crime_risk_delta=_lerp(cur.crime_risk_delta, nxt.crime_risk_delta, factor),
        land_value_delta=_lerp(cur.land_value_delta, nxt.land_value_delta, factor),
        water_demand_delta=_lerp(cur.water_demand_delta, nxt.water_demand_delta, factor),
        traffic_delta=_lerp(cur.traffic_delta, nxt.traffic_delta, factor),
        education_coverage_delta=_lerp(cur.education_coverage_delta, nxt.education_coverage_delta, factor),
        happiness_delta=_lerp(cur.happiness_delta, nxt.happiness_delta, factor),
    )


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t

from pydantic import BaseModel

from backend.app.schemas.response import GameEffect


class VacancyItem(BaseModel):
    id: str
    business_name: str
    title: str
    salary_per_hour: float
    min_education: str
    energy_cost: int


class VacanciesData(BaseModel):
    vacancies: list[VacancyItem]


class BusinessMarketItem(BaseModel):
    id: str
    name: str
    type: str
    cash_balance: float
    purchase_price: float


class BusinessMarketData(BaseModel):
    businesses: list[BusinessMarketItem]


class BusinessBlueprintItem(BaseModel):
    id: str
    code: str
    name: str
    category: str
    business_type: str
    project_type: str
    description: str
    difficulty: str
    allowed_land_types: list[str]
    allowed_zoning_types: list[str]
    min_area_hectares: float
    construction_cost: float
    opening_fee: float
    recommended_cash_reserve: float
    daily_profit_min: float
    daily_profit_max: float
    upkeep_daily: float
    risk_level: int
    risks: list[str]
    metric_effects: dict[str, int]
    visual_archetype: str
    style_tags: list[str]
    player_hints: list[str]


class BusinessBlueprintsData(BaseModel):
    blueprints: list[BusinessBlueprintItem]


class SportsClubItem(BaseModel):
    id: str
    name: str
    sport_type: str
    salary_per_match: float
    league_points: int


class SportsClubsData(BaseModel):
    clubs: list[SportsClubItem]


class ExamQuestionData(BaseModel):
    id: int
    text: str
    options: list[str]


class ExamInfoData(BaseModel):
    exam_id: str
    title: str
    cost_to_take: float
    passing_score: int
    time_limit_seconds: int
    description: str
    questions: list[ExamQuestionData]


class PlayerActionsData(BaseModel):
    can_apply_job: bool
    can_work: bool
    can_sleep: bool
    can_eat: bool
    can_buy_business: bool
    can_collect_dividend: bool
    can_join_sports: bool
    can_train_sports: bool
    can_take_exam: bool


class OwnedBusinessSnapshot(BaseModel):
    id: str
    name: str
    type: str
    cash_balance: float


class SportsContractSnapshot(BaseModel):
    club: str
    strength: int
    stamina: int
    salary_per_match: float


class PlayerOnboardingData(BaseModel):
    stage: str
    completed: bool
    title: str
    narrative: str
    available_choices: list[str]
    police_report_status: str
    police_recovery_amount: float | None
    police_recovery_available_at: str | None


class PlayerSnapshotData(BaseModel):
    id: str
    username: str
    balance: float
    energy: int
    mood: int
    hunger: int
    education_level: str
    diploma_verified: bool
    job: str
    job_id: str | None
    hostel: str
    owned_businesses: list[OwnedBusinessSnapshot]
    sports_contract: SportsContractSnapshot | None
    onboarding: PlayerOnboardingData
    actions: PlayerActionsData
    goal_effects: list[GameEffect]


class CityNewsItem(BaseModel):
    type: str
    title: str
    message: str
    severity: str
    priority: int


class CityDistrictItem(BaseModel):
    id: str
    code: str
    name: str
    zone_type: str
    description: str
    display_order: int
    land_available_hectares: float
    rent_level: int
    job_supply: int
    crime_risk: int
    traffic: int
    service_coverage: int
    medical_coverage: int
    land_value: int
    desirability: int


class CityStatusData(BaseModel):
    id: str
    name: str
    treasury_balance: float
    tax_rate_income: float
    tax_rate_property: float
    inflation_rate: float
    news: list[CityNewsItem]
    districts: list[CityDistrictItem]


class LandParcelItem(BaseModel):
    id: str
    city_id: str
    district_id: str
    district_code: str
    district_name: str
    code: str
    label: str
    land_type: str
    zoning_type: str
    area_hectares: float
    base_price_per_hectare: float
    current_price: float
    status: str
    owner_player_id: str | None


class LandParcelsData(BaseModel):
    parcels: list[LandParcelItem]


class MayorPolicyIssueData(BaseModel):
    code: str
    message: str


class BuildingApplicationData(BaseModel):
    id: str
    city_id: str
    district_id: str
    land_parcel_id: str
    business_blueprint_id: str | None
    applicant_player_id: str
    proposed_name: str
    project_type: str
    land_area_hectares: float
    expected_jobs: int
    traffic_load: int
    service_load: int
    medical_load: int
    public_benefit: int
    status: str
    mayor_score: int
    mayor_summary: str
    mayor_issues: list[MayorPolicyIssueData]
    mayor_questions: list[str]


class BuildingItem(BaseModel):
    id: str
    city_id: str
    district_id: str
    land_parcel_id: str
    source_application_id: str
    business_blueprint_id: str | None
    business_id: str | None
    owner_player_id: str
    name: str
    project_type: str
    status: str
    operating_status: str


class LandPurchaseActionData(PlayerSnapshotData):
    land_parcel: LandParcelItem


class BuildingActivationActionData(PlayerSnapshotData):
    building: BuildingItem


class BuildingOpenActionData(PlayerSnapshotData):
    building: BuildingItem
    opening_fee: float


class BuildingRepairActionData(PlayerSnapshotData):
    building: BuildingItem
    repair_fee: float


class BuildingPortfolioItem(BaseModel):
    id: str
    city_id: str
    district_id: str
    district_code: str
    district_name: str
    land_parcel_id: str
    land_parcel_code: str
    land_parcel_label: str
    source_application_id: str
    business_blueprint_id: str | None
    blueprint_code: str | None
    blueprint_name: str | None
    blueprint_category: str | None
    business_id: str | None
    business_type: str | None
    business_cash_balance: float | None
    owner_player_id: str
    name: str
    project_type: str
    status: str
    operating_status: str
    opening_fee: float
    repair_fee: float
    upkeep_daily: float
    available_actions: list[str]


class BuildingPortfolioData(BaseModel):
    buildings: list[BuildingPortfolioItem]


class DayTickCityData(BaseModel):
    id: str
    inflation_rate: float
    treasury_balance: float


class DayTickStatsData(BaseModel):
    players_updated: int
    rent_collected: float
    homeless_players: int
    hungry_players: int
    building_upkeep_charged: float
    buildings_upkeep_charged: int
    buildings_upkeep_failed: int
    active_money_before: float
    active_money_after: float


class DayTickData(BaseModel):
    city: DayTickCityData
    stats: DayTickStatsData
    news: list[CityNewsItem]


class CityBalanceSnapshot(BaseModel):
    treasury_balance: float


class BusinessActionSnapshot(BaseModel):
    id: str
    name: str
    type: str
    cash_balance: float
    purchase_price: float | None = None


class SportsStatsData(BaseModel):
    strength: int
    stamina: int


class ExamSubmissionDetailData(BaseModel):
    question_id: int
    correct: bool
    explanation: str


class WorkActionData(PlayerSnapshotData):
    city: CityBalanceSnapshot


class BusinessBuyActionData(PlayerSnapshotData):
    business: BusinessActionSnapshot


class BusinessDividendActionData(PlayerSnapshotData):
    business: BusinessActionSnapshot
    dividend: float


class SportsTrainActionData(PlayerSnapshotData):
    sports_stats: SportsStatsData


class ExamSubmitActionData(PlayerSnapshotData):
    passed: bool
    score: str
    details: list[ExamSubmissionDetailData]

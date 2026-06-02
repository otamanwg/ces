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
    actions: PlayerActionsData
    goal_effects: list[GameEffect]


class CityNewsItem(BaseModel):
    type: str
    title: str
    message: str
    severity: str
    priority: int


class CityStatusData(BaseModel):
    id: str
    name: str
    treasury_balance: float
    tax_rate_income: float
    tax_rate_property: float
    inflation_rate: float
    news: list[CityNewsItem]


class DayTickCityData(BaseModel):
    id: str
    inflation_rate: float
    treasury_balance: float


class DayTickStatsData(BaseModel):
    players_updated: int
    rent_collected: float
    homeless_players: int
    hungry_players: int
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

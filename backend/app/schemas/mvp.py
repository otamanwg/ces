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

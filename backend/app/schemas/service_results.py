from pydantic import BaseModel


class BusinessServiceSnapshot(BaseModel):
    id: str
    name: str
    type: str
    cash_balance: float
    purchase_price: float | None = None


class PlayerBalanceServiceSnapshot(BaseModel):
    balance: float


class PlayerMealServiceSnapshot(PlayerBalanceServiceSnapshot):
    hunger: int
    mood: int


class PlayerEnergyServiceSnapshot(PlayerBalanceServiceSnapshot):
    energy: int


class PlayerEducationServiceSnapshot(PlayerBalanceServiceSnapshot):
    education_level: str


class BusinessPurchaseServiceResult(BaseModel):
    success: bool
    message: str
    business: BusinessServiceSnapshot
    player: PlayerBalanceServiceSnapshot


class BusinessDividendServiceResult(BaseModel):
    success: bool
    message: str
    business: BusinessServiceSnapshot
    player: PlayerBalanceServiceSnapshot
    dividend: float


class SportsStatsServiceSnapshot(BaseModel):
    strength: int
    stamina: int


class SportsTrainServiceResult(BaseModel):
    success: bool
    message: str
    player: PlayerEnergyServiceSnapshot
    stats: SportsStatsServiceSnapshot


class MealPurchaseServiceResult(BaseModel):
    success: bool
    message: str
    player: PlayerMealServiceSnapshot


class ExamSubmissionDetailServiceResult(BaseModel):
    question_id: int
    correct: bool
    explanation: str


class ExamSubmissionServiceResult(BaseModel):
    success: bool
    passed: bool
    score: str
    message: str
    details: list[ExamSubmissionDetailServiceResult]
    player: PlayerEducationServiceSnapshot

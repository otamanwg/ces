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


class PlayerWorkServiceSnapshot(PlayerEnergyServiceSnapshot):
    hunger: int


class PlayerRestServiceSnapshot(PlayerWorkServiceSnapshot):
    mood: int


class PlayerEducationServiceSnapshot(PlayerBalanceServiceSnapshot):
    education_level: str


class CityTreasuryServiceSnapshot(BaseModel):
    treasury_balance: float


class DayTickCityServiceSnapshot(CityTreasuryServiceSnapshot):
    id: str
    inflation_rate: float


class DayTickStatsServiceSnapshot(BaseModel):
    players_updated: int
    rent_collected: float
    homeless_players: int
    hungry_players: int
    active_money_before: float
    active_money_after: float


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


class SportsContractServiceResult(BaseModel):
    success: bool
    message: str


class SportsTrainServiceResult(BaseModel):
    success: bool
    message: str
    player: PlayerEnergyServiceSnapshot
    stats: SportsStatsServiceSnapshot


class SportsLeagueMatchServiceResult(BaseModel):
    match: str
    result: str
    winner_id: str


class SportsLeagueMessageServiceResult(BaseModel):
    message: str


class WorkShiftServiceResult(BaseModel):
    success: bool
    message: str
    player: PlayerWorkServiceSnapshot
    city: CityTreasuryServiceSnapshot


class RentPaymentServiceResult(BaseModel):
    success: bool
    message: str
    player: PlayerRestServiceSnapshot


class DayTickServiceResult(BaseModel):
    success: bool
    message: str
    city: DayTickCityServiceSnapshot
    stats: DayTickStatsServiceSnapshot


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

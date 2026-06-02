from pydantic import BaseModel


class BusinessServiceSnapshot(BaseModel):
    id: str
    name: str
    type: str
    cash_balance: float
    purchase_price: float | None = None


class PlayerBalanceServiceSnapshot(BaseModel):
    balance: float


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

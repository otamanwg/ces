from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import City, Player, SportsClub
from backend.app.schemas.frozen import FrozenSportsClubsResponse, FrozenSportsMatchesResponse
from backend.app.services.advanced import (
    buy_insurance_policy,
    donate_to_lobby_fund,
    process_daily_loan_installments_and_collectors,
    toggle_labor_union_strike,
)
from backend.app.services.education import purchase_fake_diploma, run_police_audit
from backend.app.services.sports import sign_athlete_contract, simulate_league_matches, train_at_gym

router = APIRouter(prefix="/api/frozen", tags=["frozen"])


class GymTrain(BaseModel):
    player_id: str
    stat_type: str


class SportsContractApply(BaseModel):
    player_id: str
    club_id: str
    salary: float


class UnionStrikeToggle(BaseModel):
    business_id: str
    union_name: str


class BuyInsurance(BaseModel):
    player_id: str
    business_id: str
    provider_business_id: str
    coverage: float
    premium: float


class CartelLobby(BaseModel):
    cartel_name: str
    industry: str
    player_id: str
    amount: float


@router.post("/shadow/buy_diploma/{player_id}")
def buy_fake(player_id: str, db: Session = Depends(get_db)):
    res = purchase_fake_diploma(db, player_id)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["message"])
    return res


@router.post("/police/audit/{player_id}")
def police_audit(player_id: str, db: Session = Depends(get_db)):
    return run_police_audit(db, player_id)


@router.get("/sports/clubs")
def get_sports_clubs(db: Session = Depends(get_db)):
    clubs = db.query(SportsClub).all()
    return FrozenSportsClubsResponse(
        clubs=[
            {
                "id": str(c.id),
                "name": c.name,
                "sport_type": c.sport_type,
                "owner": db.query(Player).filter(Player.id == c.owner_player_id).first().username
                if c.owner_player_id
                else "ШІ-Управління",
                "cash_balance": float(c.cash_balance),
                "stadium_capacity": c.stadium_capacity,
                "ticket_price": float(c.ticket_price),
                "league_points": c.league_points,
            }
            for c in clubs
        ]
    ).model_dump()


@router.post("/sports/train")
def train_gym(data: GymTrain, db: Session = Depends(get_db)):
    res = train_at_gym(db, data.player_id, data.stat_type)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["message"])
    return res


@router.post("/sports/sign_contract")
def sign_contract(data: SportsContractApply, db: Session = Depends(get_db)):
    res = sign_athlete_contract(db, data.player_id, data.club_id, data.salary)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["message"])
    return res


@router.post("/sports/simulate_matches")
def simulate_matches(db: Session = Depends(get_db)):
    city = db.query(City).first()
    if not city:
        raise HTTPException(status_code=404, detail="Місто не знайдене")
    res = simulate_league_matches(db, city.id)
    return FrozenSportsMatchesResponse(success=True, matches=res).model_dump()


@router.post("/advanced/union/strike")
def toggle_strike(data: UnionStrikeToggle, db: Session = Depends(get_db)):
    return toggle_labor_union_strike(db, data.business_id, data.union_name)


@router.post("/advanced/insurance/buy")
def buy_insurance(data: BuyInsurance, db: Session = Depends(get_db)):
    res = buy_insurance_policy(
        db, data.player_id, data.business_id, data.provider_business_id, data.coverage, data.premium
    )
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["message"])
    return res


@router.post("/advanced/loans/daily_pay/{player_id}")
def process_loans_daily(player_id: str, db: Session = Depends(get_db)):
    return process_daily_loan_installments_and_collectors(db, player_id)


@router.post("/advanced/cartel/lobby")
def lobby_cartel(data: CartelLobby, db: Session = Depends(get_db)):
    city = db.query(City).first()
    if not city:
        raise HTTPException(status_code=404, detail="Місто не знайдене")
    res = donate_to_lobby_fund(db, data.cartel_name, city.id, data.industry, data.player_id, data.amount)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["message"])
    return res

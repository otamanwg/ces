from pydantic import BaseModel

from backend.app.schemas.service_results import SportsLeagueMatchServiceResult, SportsLeagueMessageServiceResult


class FrozenSportsMatchesResponse(BaseModel):
    success: bool
    matches: list[SportsLeagueMatchServiceResult | SportsLeagueMessageServiceResult]


class FrozenSportsClubItem(BaseModel):
    id: str
    name: str
    sport_type: str
    owner: str
    cash_balance: float
    stadium_capacity: int
    ticket_price: float
    league_points: int


class FrozenSportsClubsResponse(BaseModel):
    clubs: list[FrozenSportsClubItem]

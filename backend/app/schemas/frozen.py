from pydantic import BaseModel

from backend.app.schemas.service_results import SportsLeagueMatchServiceResult, SportsLeagueMessageServiceResult


class FrozenSportsMatchesResponse(BaseModel):
    success: bool
    matches: list[SportsLeagueMatchServiceResult | SportsLeagueMessageServiceResult]

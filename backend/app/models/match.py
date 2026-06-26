from pydantic import BaseModel


class Match(BaseModel):
    match_id: str
    round: str
    match_number: int
    home_team: str
    away_team: str
    home_score: int | None = None
    away_score: int | None = None
    pk_home_score: int | None = None
    pk_away_score: int | None = None
    pk_winner: str | None = None
    status: str
    kickoff_time: str


# Match is used directly as the response model for individual match endpoints.
MatchResponse = Match


class MatchesByRoundResponse(BaseModel):
    rounds: dict[str, list[Match]]

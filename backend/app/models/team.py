from pydantic import BaseModel


class TeamRecord(BaseModel):
    team: str
    wins: int
    draws: int
    losses: int
    goals_for: int
    goals_against: int


class TeamRecordsResponse(BaseModel):
    records: dict[str, TeamRecord]

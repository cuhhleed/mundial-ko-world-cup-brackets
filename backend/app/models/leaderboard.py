from pydantic import BaseModel


class LeaderboardEntry(BaseModel):
    rank: int
    display_name: str
    total_points: int


class LeaderboardResponse(BaseModel):
    entries: list[LeaderboardEntry]
    total_participants: int


class MyRankResponse(BaseModel):
    rank: int
    total_points: int
    total_participants: int

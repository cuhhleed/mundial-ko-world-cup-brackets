from pydantic import BaseModel


class SlotPrediction(BaseModel):
    teams: list[str]
    winner: str
    scores: dict[str, int] | None = None
    pk_winner: str | None = None
    pk_scores: dict[str, int] | None = None


class Bracket(BaseModel):
    bracket_id: str
    user_id: str
    predictions: dict[str, SlotPrediction]
    total_points: int = 0
    status: str = "submitted"
    created_at: str

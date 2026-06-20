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
    locked_slots: list[str] = []
    total_points: int = 0
    status: str = "submitted"
    created_at: str


class SlotTemplate(BaseModel):
    slot_id: str
    teams: list[str] | None
    status: str
    result: SlotPrediction | None = None


class BracketTemplate(BaseModel):
    slots: dict[str, SlotTemplate]


class SlotDetail(BaseModel):
    prediction: SlotPrediction
    result: SlotPrediction | None = None
    points: int | None = None


class BracketResponse(BaseModel):
    bracket_id: str
    user_id: str
    slots: dict[str, SlotDetail]
    locked_slots: list[str] = []
    total_points: int = 0
    status: str
    created_at: str

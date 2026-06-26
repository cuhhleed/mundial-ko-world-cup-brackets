from fastapi import APIRouter

from app.models.team import TeamRecordsResponse
from app.services.teams import compute_team_records

router = APIRouter(prefix="/api/teams")


@router.get("/records", response_model=TeamRecordsResponse)
async def get_team_records() -> TeamRecordsResponse:
    records = compute_team_records()
    return TeamRecordsResponse(records=records)

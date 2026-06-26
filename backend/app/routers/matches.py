from fastapi import APIRouter, HTTPException

from app.models.match import Match, MatchesByRoundResponse
from app.services.matches import get_all_matches_with_live_overlay, get_match_by_id

router = APIRouter(prefix="/api/matches")


@router.get("", response_model=MatchesByRoundResponse)
async def list_matches() -> MatchesByRoundResponse:
    matches = await get_all_matches_with_live_overlay()

    rounds: dict[str, list[Match]] = {}
    for match in matches.values():
        rounds.setdefault(match.round, []).append(match)

    return MatchesByRoundResponse(rounds=rounds)


@router.get("/{match_id}", response_model=Match)
async def get_match(match_id: str) -> Match:
    match = await get_match_by_id(match_id)
    if match is None:
        raise HTTPException(status_code=404, detail="Match not found")
    return match

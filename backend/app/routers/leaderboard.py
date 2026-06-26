from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth.dependencies import require_user
from app.models.leaderboard import LeaderboardResponse, MyRankResponse
from app.models.user import AuthenticatedUser
from app.services import leaderboard as leaderboard_service

router = APIRouter(prefix="/api/leaderboard")


@router.get("", response_model=LeaderboardResponse)
async def get_leaderboard(
    limit: int = Query(default=50, ge=1, le=200),
) -> LeaderboardResponse:
    return await leaderboard_service.get_top(limit)


@router.get("/me", response_model=MyRankResponse)
async def get_my_rank(
    user: AuthenticatedUser = Depends(require_user),
) -> MyRankResponse:
    result = await leaderboard_service.get_my_rank(user.user_id)
    if result is None:
        raise HTTPException(status_code=404, detail="User has no leaderboard ranking")
    return result

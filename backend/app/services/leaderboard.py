import asyncio

import app.db.cache as cache
from app.logging import get_logger
from app.models.leaderboard import LeaderboardEntry, LeaderboardResponse, MyRankResponse
from app.services.users import batch_get_display_names

logger = get_logger("leaderboard")


async def get_top(limit: int) -> LeaderboardResponse:
    top_entries, total = await asyncio.gather(
        cache.get_leaderboard_top(limit),
        cache.get_leaderboard_count(),
    )

    user_ids = [uid for uid, _score in top_entries]
    display_names = await asyncio.to_thread(batch_get_display_names, user_ids)

    entries = [
        LeaderboardEntry(
            rank=rank,
            display_name=display_names.get(uid, "Unknown"),
            total_points=int(score),
        )
        for rank, (uid, score) in enumerate(top_entries, start=1)
    ]

    return LeaderboardResponse(entries=entries, total_participants=total)


async def get_my_rank(user_id: str) -> MyRankResponse | None:
    rank, score, total = await asyncio.gather(
        cache.get_leaderboard_rank(user_id),
        cache.get_leaderboard_score(user_id),
        cache.get_leaderboard_count(),
    )

    if rank is None:
        return None

    return MyRankResponse(
        rank=rank + 1,
        total_points=int(score),
        total_participants=total,
    )

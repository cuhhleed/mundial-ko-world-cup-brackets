from app.espn.adapter import get_match_schedule
from app.logging import get_logger
from app.services.matches import get_all_matches, put_match

logger = get_logger("schedule-loader")


def load_initial_schedule(start_date: str, end_date: str) -> tuple[int, int]:
    """Fetch the match schedule from ESPN and write or update matches in DynamoDB.

    Writes new matches not already present. For matches that already exist and
    are still scheduled, updates them if the team codes have changed (e.g. when
    placeholder group-stage codes are resolved to real FIFA codes).

    Returns a tuple of (written, updated).
    """
    espn_matches = get_match_schedule(start_date, end_date)
    existing_matches = get_all_matches()

    written = 0
    updated = 0
    for match_id, match in espn_matches.items():
        if match_id not in existing_matches:
            put_match(match)
            written += 1
        else:
            existing = existing_matches[match_id]
            if existing.status == "scheduled" and (
                existing.home_team != match.home_team
                or existing.away_team != match.away_team
            ):
                put_match(match)
                updated += 1

    logger.info(
        "schedule_loaded",
        total_from_espn=len(espn_matches),
        already_existing=len(existing_matches),
        written=written,
        updated=updated,
    )
    return written, updated

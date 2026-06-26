from app.espn.adapter import get_match_schedule
from app.logging import get_logger
from app.services.matches import get_all_matches, put_match

logger = get_logger("schedule-loader")


def load_initial_schedule(start_date: str, end_date: str) -> int:
    """Fetch the match schedule from ESPN and write only new matches to DynamoDB.

    Compares ESPN results against existing DynamoDB records and writes only
    matches not already present. Returns the count of matches written.
    """
    espn_matches = get_match_schedule(start_date, end_date)
    existing_matches = get_all_matches()

    written = 0
    for match_id, match in espn_matches.items():
        if match_id not in existing_matches:
            put_match(match)
            written += 1

    logger.info(
        "schedule_loaded",
        total_from_espn=len(espn_matches),
        already_existing=len(existing_matches),
        written=written,
    )
    return written

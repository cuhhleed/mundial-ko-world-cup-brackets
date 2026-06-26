import json
from pathlib import Path

from app.services.matches import get_all_matches

_R32_SLOT_COUNT = 16


def load_r32_matchups() -> dict[str, tuple[str, str]]:
    """Load R32 matchups from DynamoDB matches, falling back to the bundled JSON."""
    matches = get_all_matches()
    r32: dict[str, tuple[str, str]] = {}
    for match_id, match in matches.items():
        if match_id.startswith("R32-"):
            r32[match_id] = (match.home_team, match.away_team)

    if len(r32) == _R32_SLOT_COUNT:
        return r32

    return _load_from_json()


def _load_from_json() -> dict[str, tuple[str, str]]:
    path = Path(__file__).parent / "r32_matchups.json"
    with path.open() as f:
        raw: dict[str, list[str]] = json.load(f)
    return {slot: (teams[0], teams[1]) for slot, teams in raw.items()}

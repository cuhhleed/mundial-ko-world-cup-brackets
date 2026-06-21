import json
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def load_r32_matchups() -> dict[str, tuple[str, str]]:
    """Load R32 matchups from the bundled JSON config, cached for the process lifetime."""
    path = Path(__file__).parent / "r32_matchups.json"
    with path.open() as f:
        raw: dict[str, list[str]] = json.load(f)
    return {slot: (teams[0], teams[1]) for slot, teams in raw.items()}

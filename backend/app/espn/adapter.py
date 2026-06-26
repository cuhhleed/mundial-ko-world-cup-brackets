import json
import re
from functools import lru_cache
from pathlib import Path

from app.espn.client import fetch_live_scores, fetch_schedule, fetch_scoreboard
from app.models.match import Match

_STAGE_TO_ROUND = {
    "round-of-32": "R32",
    "round-of-16": "R16",
    "quarterfinals": "QF",
    "semifinals": "SF",
    "final": "FINAL",
    "third-place": "TP",
    "3rd-place-match": "TP",
}

_STATUS_MAP = {
    "pre": "scheduled",
    "in": "live",
    "post": "completed",
}

_PLACEHOLDER_RE = re.compile(r"^([12])([A-P])$")


def _normalize_team_code(espn_code: str) -> str:
    """Swap placeholder codes like '1A' → 'A1'. FIFA codes like 'ARG' pass through."""
    match = _PLACEHOLDER_RE.match(espn_code)
    if match:
        return match.group(2) + match.group(1)
    return espn_code


def _map_status(espn_state: str) -> str:
    """Map ESPN state string to internal status. Defaults to 'scheduled'."""
    return _STATUS_MAP.get(espn_state, "scheduled")


def _parse_slot_id(slot_id: str) -> tuple[str, int]:
    """Parse slot_id into (round, match_number). FINAL and TP are single matches."""
    if slot_id in ("FINAL", "TP"):
        return (slot_id, 1)
    round_name, number = slot_id.rsplit("-", 1)
    return (round_name, int(number))


@lru_cache(maxsize=1)
def _load_event_map() -> dict[str, str]:
    """Load the static ESPN event ID → slot_id mapping. Returns {} if missing or empty."""
    map_path = Path(__file__).parent / "espn_event_map.json"
    try:
        data = json.loads(map_path.read_text())
        return data if data else {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _assign_slots_by_stage(events: list[dict]) -> list[tuple[dict, str]]:
    """
    Group events by stage→round, sort each group chronologically by event.date,
    and assign sequential slot IDs (e.g. 'R32-1', 'R32-2', ...).
    FINAL and TP get their round name as the slot_id.
    """
    groups: dict[str, list[dict]] = {}
    for event in events:
        stage = event.get("season", {}).get("slug", "")
        round_name = _STAGE_TO_ROUND.get(stage, "GRP")
        groups.setdefault(round_name, []).append(event)

    result: list[tuple[dict, str]] = []
    for round_name, round_events in groups.items():
        sorted_events = sorted(round_events, key=lambda e: e.get("date", ""))
        for i, event in enumerate(sorted_events, start=1):
            if round_name in ("FINAL", "TP"):
                slot_id = round_name
            else:
                slot_id = f"{round_name}-{i}"
            result.append((event, slot_id))

    return result


def espn_event_to_match(event: dict, slot_id: str) -> Match:
    """Convert a single ESPN event dict to a Match model instance."""
    competition = event.get("competitions", [{}])[0]
    competitors = competition.get("competitors", [])

    # Identify home and away by the homeAway field, NOT array position
    home_competitor: dict = {}
    away_competitor: dict = {}
    for competitor in competitors:
        if competitor.get("homeAway") == "home":
            home_competitor = competitor
        elif competitor.get("homeAway") == "away":
            away_competitor = competitor

    home_team = _normalize_team_code(home_competitor.get("team", {}).get("abbreviation", ""))
    away_team = _normalize_team_code(away_competitor.get("team", {}).get("abbreviation", ""))

    state = competition.get("status", {}).get("type", {}).get("state", "pre")
    status = _map_status(state)

    # Parse regulation scores
    def _parse_score(competitor: dict) -> int | None:
        raw = competitor.get("score")
        if raw is None or raw == "":
            return None
        try:
            return int(raw)
        except (ValueError, TypeError):
            return None

    home_score = _parse_score(home_competitor)
    away_score = _parse_score(away_competitor)

    # Parse shootout scores
    def _parse_shootout(competitor: dict) -> int | None:
        raw = competitor.get("shootoutScore")
        if raw is None:
            return None
        try:
            return int(raw)
        except (ValueError, TypeError):
            return None

    pk_home_score = _parse_shootout(home_competitor)
    pk_away_score = _parse_shootout(away_competitor)

    # Derive pk_winner from shootout scores
    pk_winner: str | None = None
    if pk_home_score is not None and pk_away_score is not None:
        if pk_home_score > pk_away_score:
            pk_winner = home_team
        elif pk_away_score > pk_home_score:
            pk_winner = away_team

    round_name, match_number = _parse_slot_id(slot_id)

    return Match(
        match_id=slot_id,
        round=round_name,
        match_number=match_number,
        home_team=home_team,
        away_team=away_team,
        home_score=home_score,
        away_score=away_score,
        pk_home_score=pk_home_score,
        pk_away_score=pk_away_score,
        pk_winner=pk_winner,
        status=status,
        kickoff_time=event.get("date", ""),
    )


def espn_events_to_matches(events: list[dict]) -> dict[str, Match]:
    """
    Batch-convert ESPN events to a slot_id → Match dict.
    Uses static event map for known IDs, heuristic slot assignment otherwise.
    """
    event_map = _load_event_map()
    result: dict[str, Match] = {}
    unmapped: list[dict] = []

    for event in events:
        event_id = str(event.get("id", ""))
        slot_id = event_map.get(event_id)
        if slot_id:
            result[slot_id] = espn_event_to_match(event, slot_id)
        else:
            unmapped.append(event)

    if unmapped:
        for event, slot_id in _assign_slots_by_stage(unmapped):
            result[slot_id] = espn_event_to_match(event, slot_id)

    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_live_matches() -> dict[str, Match]:
    """Return all currently live matches, keyed by slot_id."""
    events = fetch_live_scores()
    return espn_events_to_matches(events)


def get_completed_results() -> dict[str, Match]:
    """Return all completed matches from today's scoreboard, keyed by slot_id."""
    events = fetch_scoreboard()
    completed = [
        event
        for event in events
        if event.get("competitions", [{}])[0].get("status", {}).get("type", {}).get("state")
        == "post"
    ]
    return espn_events_to_matches(completed)


def get_match_schedule(start_date: str, end_date: str) -> dict[str, Match]:
    """Return all matches in the given date range, keyed by slot_id."""
    events = fetch_schedule(start_date, end_date)
    return espn_events_to_matches(events)

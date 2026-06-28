"""
Interactive match result simulator for testing bracket progression.

Walks through every knockout match in bracket order, prompts for a score,
and writes each result to local DynamoDB as it goes. Simulates the
real-time progression of the tournament one match at a time.

Already-completed matches are shown but skipped. Later-round matchups
are derived from winners of earlier rounds.

Usage:
    python simulate_interactive.py          # targets local DynamoDB
    python simulate_interactive.py dev      # targets dev DynamoDB in AWS
"""

import asyncio
import os
import sys
from datetime import datetime, timezone

import boto3

USE_DEV = len(sys.argv) > 1 and sys.argv[1] == "dev"

if USE_DEV:
    ENVIRONMENT = "dev"
    os.environ["ENVIRONMENT"] = ENVIRONMENT
    os.environ.pop("DYNAMODB_ENDPOINT_URL", None)
    os.environ["USERS_TABLE"] = "mundial-ko-dev-users"
    os.environ["BRACKETS_TABLE"] = "mundial-ko-dev-brackets"
    os.environ["MATCHES_TABLE"] = "mundial-ko-dev-matches"
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
else:
    os.environ.setdefault("DYNAMODB_ENDPOINT_URL", "http://localhost:8001")
    ENVIRONMENT = os.getenv("ENVIRONMENT", "local")
    dynamodb = boto3.resource(
        "dynamodb",
        endpoint_url=os.getenv("DYNAMODB_ENDPOINT_URL", "http://localhost:8001"),
        region_name="localhost",
        aws_access_key_id="DUMMYIDEXAMPLE",
        aws_secret_access_key="DUMMYSECRETANDKEYEXAMPLE",
    )

PROJECT_NAME = os.getenv("PROJECT_NAME", "mundial-ko")
TABLE_NAME = f"{PROJECT_NAME}-{ENVIRONMENT}-matches"
table = dynamodb.Table(TABLE_NAME)

ALL_SLOTS = (
    [f"R32-{i}" for i in range(1, 17)]
    + [f"R16-{i}" for i in range(1, 9)]
    + [f"QF-{i}" for i in range(1, 5)]
    + ["SF-1", "SF-2", "FINAL", "TP"]
)

FEEDERS = {
    "R16-1": (("R32-1", "winner"), ("R32-4", "winner")),
    "R16-2": (("R32-3", "winner"), ("R32-6", "winner")),
    "R16-3": (("R32-2", "winner"), ("R32-5", "winner")),
    "R16-4": (("R32-7", "winner"), ("R32-8", "winner")),
    "R16-5": (("R32-12", "winner"), ("R32-11", "winner")),
    "R16-6": (("R32-10", "winner"), ("R32-9", "winner")),
    "R16-7": (("R32-15", "winner"), ("R32-14", "winner")),
    "R16-8": (("R32-13", "winner"), ("R32-16", "winner")),
    "QF-1": (("R16-1", "winner"), ("R16-2", "winner")),
    "QF-2": (("R16-5", "winner"), ("R16-6", "winner")),
    "QF-3": (("R16-3", "winner"), ("R16-4", "winner")),
    "QF-4": (("R16-7", "winner"), ("R16-8", "winner")),
    "SF-1": (("QF-1", "winner"), ("QF-2", "winner")),
    "SF-2": (("QF-3", "winner"), ("QF-4", "winner")),
    "FINAL": (("SF-1", "winner"), ("SF-2", "winner")),
    "TP": (("SF-1", "loser"), ("SF-2", "loser")),
}


def load_matches() -> dict[str, dict]:
    """Scan all matches from DynamoDB into a dict keyed by match_id."""
    matches = {}
    kwargs: dict = {}
    while True:
        response = table.scan(**kwargs)
        for item in response.get("Items", []):
            matches[item["match_id"]] = item
        last = response.get("LastEvaluatedKey")
        if last is None:
            break
        kwargs["ExclusiveStartKey"] = last
    return matches


def get_winner(match: dict) -> str:
    if match.get("pk_winner"):
        return match["pk_winner"]
    if match["home_score"] > match["away_score"]:
        return match["home_team"]
    return match["away_team"]


def get_loser(match: dict) -> str:
    winner = get_winner(match)
    if match["home_team"] == winner:
        return match["away_team"]
    return match["home_team"]


def get_outcome_team(match: dict, outcome: str) -> str:
    if outcome == "winner":
        return get_winner(match)
    return get_loser(match)


def derive_teams(slot_id: str, results: dict[str, dict]) -> tuple[str, str] | None:
    """Derive home/away teams for a downstream slot from feeder results."""
    if slot_id not in FEEDERS:
        return None

    (f1_id, f1_outcome), (f2_id, f2_outcome) = FEEDERS[slot_id]
    f1 = results.get(f1_id)
    f2 = results.get(f2_id)

    if not f1 or not f2:
        return None

    return get_outcome_team(f1, f1_outcome), get_outcome_team(f2, f2_outcome)


def format_score(match: dict) -> str:
    line = f"{match['home_score']}-{match['away_score']}"
    if match.get("pk_home_score") is not None:
        line += f" (PK {match['pk_home_score']}-{match['pk_away_score']})"
    return line


def prompt_score(slot_id: str, home: str, away: str) -> dict | None:
    """Prompt the user for a match result. Returns the result dict or None to skip."""
    print(f"\n{'─' * 50}")
    print(f"  {slot_id}:  {home}  vs  {away}")
    print(f"{'─' * 50}")

    while True:
        raw = input("  Score (e.g. 2-1), [s]kip, or [q]uit: ").strip().lower()

        if raw in ("q", "quit"):
            return None
        if raw in ("s", "skip"):
            print(f"  Skipped {slot_id}.")
            return "skip"

        parts = raw.split("-")
        if len(parts) != 2:
            print("  Invalid format. Use home_score-away_score (e.g. 2-1)")
            continue

        try:
            home_score = int(parts[0])
            away_score = int(parts[1])
        except ValueError:
            print("  Scores must be integers.")
            continue

        if home_score < 0 or away_score < 0:
            print("  Scores must be non-negative.")
            continue

        result = {
            "home_score": home_score,
            "away_score": away_score,
        }

        if home_score == away_score:
            pk = prompt_pk(home, away)
            if pk is None:
                return None
            result.update(pk)

        return result


def prompt_pk(home: str, away: str) -> dict | None:
    """Prompt for penalty shootout result after a draw."""
    print("  Draw! Enter penalty result.")

    while True:
        raw = input("  PK score (e.g. 5-4), or [q]uit: ").strip().lower()

        if raw in ("q", "quit"):
            return None

        parts = raw.split("-")
        if len(parts) != 2:
            print("  Invalid format. Use pk_home-pk_away (e.g. 5-4)")
            continue

        try:
            pk_home = int(parts[0])
            pk_away = int(parts[1])
        except ValueError:
            print("  Scores must be integers.")
            continue

        if pk_home < 0 or pk_away < 0:
            print("  Scores must be non-negative.")
            continue

        if pk_home == pk_away:
            print("  PK cannot end in a draw.")
            continue

        pk_winner = home if pk_home > pk_away else away
        return {
            "pk_home_score": pk_home,
            "pk_away_score": pk_away,
            "pk_winner": pk_winner,
        }


def write_result(
    slot_id: str,
    rnd: str,
    match_number: int,
    home: str,
    away: str,
    result: dict,
    existing: dict | None,
):
    """Write the completed match to DynamoDB."""
    item = {
        "match_id": slot_id,
        "round": rnd,
        "match_number": match_number,
        "home_team": home,
        "away_team": away,
        "home_score": result["home_score"],
        "away_score": result["away_score"],
        "status": "completed",
        "kickoff_time": (
            existing.get("kickoff_time", datetime.now(timezone.utc).isoformat())
            if existing
            else datetime.now(timezone.utc).isoformat()
        ),
    }

    if "pk_home_score" in result:
        item["pk_home_score"] = result["pk_home_score"]
        item["pk_away_score"] = result["pk_away_score"]
        item["pk_winner"] = result["pk_winner"]

    table.put_item(Item=item)

    winner = result.get("pk_winner") or (
        home if result["home_score"] > result["away_score"] else away
    )
    score_line = format_score(item)
    print(f"  ✓ {slot_id}: {home} {score_line} {away}  →  {winner}")

    return item


async def _run_scoring():
    from app.db.cache import clear_leaderboard, connect, disconnect, update_leaderboard
    from app.services.brackets import rescore_all_brackets

    result = rescore_all_brackets()
    if result["updates"]:
        await connect()
        await clear_leaderboard()
        for _, user_id, total_points in result["updates"]:
            await update_leaderboard(user_id, total_points)
        await disconnect()
    return result


def trigger_scoring():
    if USE_DEV:
        print("  (skipping scoring — Redis not reachable outside VPC)")
        return
    result = asyncio.run(_run_scoring())
    scored = result["scored"]
    updated = len(result["updates"])
    print(f"  Scored {scored} brackets, updated {updated} leaderboard entries")
    for err in result["errors"]:
        print(f"  Error: {err}")


def parse_slot(slot_id: str) -> tuple[str, int]:
    """Extract round and match_number from a slot_id."""
    if slot_id in ("FINAL", "TP"):
        return slot_id, 1
    rnd, num = slot_id.rsplit("-", 1)
    return rnd, int(num)


def run():
    print("Loading matches from DynamoDB...")
    db_matches = load_matches()

    results: dict[str, dict] = {}
    completed_count = 0
    simulated_count = 0

    print(f"Found {len(db_matches)} matches in database.\n")

    current_round = None

    for slot_id in ALL_SLOTS:
        rnd, match_number = parse_slot(slot_id)

        if rnd != current_round:
            current_round = rnd
            print(f"\n{'═' * 50}")
            print(f"  {rnd}")
            print(f"{'═' * 50}")

        existing = db_matches.get(slot_id)

        if existing and existing.get("status") == "completed":
            results[slot_id] = existing
            winner = get_winner(existing)
            score_line = format_score(existing)
            print(
                f"  [done] {slot_id}: {existing['home_team']} {score_line} {existing['away_team']}  →  {winner}"
            )
            completed_count += 1
            continue

        if slot_id in FEEDERS:
            teams = derive_teams(slot_id, results)
            if teams is None:
                print(f"  [skip] {slot_id}: feeders not yet resolved")
                continue
            home, away = teams
        elif existing:
            home = existing["home_team"]
            away = existing["away_team"]
        else:
            print(f"  [skip] {slot_id}: no match data in database")
            continue

        result = prompt_score(slot_id, home, away)

        if result is None:
            print(f"\nQuitting. Simulated {simulated_count} matches this session.")
            sys.exit(0)

        if result == "skip":
            continue

        item = write_result(slot_id, rnd, match_number, home, away, result, existing)
        results[slot_id] = item
        simulated_count += 1
        trigger_scoring()

    print(
        f"\nTournament complete! Simulated {simulated_count} matches ({completed_count} were already done)."
    )


if __name__ == "__main__":
    run()

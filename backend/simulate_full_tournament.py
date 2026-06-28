"""
Simulate the entire knockout tournament to completion.

Completes all 32 matches from R32 through FINAL/TP.
Designed to run against an existing local DynamoDB with seeded scheduled matches.

Key scenarios:
  - SF-1: A1 vs O1, A1 wins on penalties (1-1, PK 4-3)
  - FINAL: A1 vs C1, A1 wins 2-1 (no penalties)

Usage:
    python simulate_full_tournament.py
"""

import os

import boto3

PROJECT_NAME = os.getenv("PROJECT_NAME", "mundial-ko")
ENVIRONMENT = os.getenv("ENVIRONMENT", "local")
TABLE_NAME = f"{PROJECT_NAME}-{ENVIRONMENT}-matches"

dynamodb = boto3.resource(
    "dynamodb",
    endpoint_url=os.getenv("DYNAMODB_ENDPOINT_URL", "http://localhost:8001"),
    region_name="localhost",
    aws_access_key_id="DUMMYIDEXAMPLE",
    aws_secret_access_key="DUMMYSECRETANDKEYEXAMPLE",
)
table = dynamodb.Table(TABLE_NAME)

# Full bracket trace:
#
# R32 winners:
#   R32-1:  A1 beat B2   | R32-9:  I1 beat J2
#   R32-2:  C1 beat D2   | R32-10: K1 beat L2
#   R32-3:  E1 beat F2   | R32-11: M1 beat N2
#   R32-4:  G1 beat H2   | R32-12: O1 beat P2
#   R32-5:  B1 beat A2   | R32-13: J1 beat I2
#   R32-6:  D1 beat C2   | R32-14: L1 beat K2
#   R32-7:  F1 beat E2   | R32-15: N1 beat M2
#   R32-8:  H1 beat G2   | R32-16: P1 beat O2
#
# R16 (corrected feeder tree):
#   R16-1: A1(R32-1) vs G1(R32-4) → A1  | R16-5: O1(R32-12) vs M1(R32-11) → O1
#   R16-2: E1(R32-3) vs D1(R32-6) → E1  | R16-6: K1(R32-10) vs I1(R32-9)  → K1
#   R16-3: C1(R32-2) vs B1(R32-5) → C1  | R16-7: N1(R32-15) vs L1(R32-14) → N1
#   R16-4: F1(R32-7) vs H1(R32-8) → H1  | R16-8: J1(R32-13) vs P1(R32-16) → J1
#
# QF (QF-1←R16-1/R16-2, QF-2←R16-5/R16-6, QF-3←R16-3/R16-4, QF-4←R16-7/R16-8):
#   QF-1: A1 vs E1 → A1   | QF-3: C1 vs H1 → C1
#   QF-2: O1 vs K1 → O1   | QF-4: N1 vs J1 → N1
#
# SF (SF-1←QF-1/QF-2, SF-2←QF-3/QF-4):
#   SF-1: A1 vs O1 → A1 (PK 1-1, 4-3)
#   SF-2: C1 vs N1 → C1 (2-0)
#
# FINAL: A1 vs C1 → A1 (2-1)
# TP:    O1 vs N1 → O1 (3-0)

RESULTS = [
    # ── R32 ───────────────────────────────────────────────────────────────────
    {
        "match_id": "R32-1",
        "round": "R32",
        "match_number": 1,
        "home_team": "A1",
        "away_team": "B2",
        "home_score": 2,
        "away_score": 1,
        "kickoff_time": "2026-06-28T16:00:00Z",
    },
    {
        "match_id": "R32-2",
        "round": "R32",
        "match_number": 2,
        "home_team": "C1",
        "away_team": "D2",
        "home_score": 1,
        "away_score": 0,
        "kickoff_time": "2026-06-28T20:00:00Z",
    },
    {
        "match_id": "R32-3",
        "round": "R32",
        "match_number": 3,
        "home_team": "E1",
        "away_team": "F2",
        "home_score": 2,
        "away_score": 0,
        "kickoff_time": "2026-06-29T16:00:00Z",
    },
    {
        "match_id": "R32-4",
        "round": "R32",
        "match_number": 4,
        "home_team": "G1",
        "away_team": "H2",
        "home_score": 3,
        "away_score": 1,
        "kickoff_time": "2026-06-29T20:00:00Z",
    },
    {
        "match_id": "R32-5",
        "round": "R32",
        "match_number": 5,
        "home_team": "B1",
        "away_team": "A2",
        "home_score": 2,
        "away_score": 0,
        "kickoff_time": "2026-06-30T16:00:00Z",
    },
    {
        "match_id": "R32-6",
        "round": "R32",
        "match_number": 6,
        "home_team": "D1",
        "away_team": "C2",
        "home_score": 1,
        "away_score": 0,
        "kickoff_time": "2026-06-30T20:00:00Z",
    },
    {
        "match_id": "R32-7",
        "round": "R32",
        "match_number": 7,
        "home_team": "F1",
        "away_team": "E2",
        "home_score": 2,
        "away_score": 1,
        "kickoff_time": "2026-07-01T16:00:00Z",
    },
    {
        "match_id": "R32-8",
        "round": "R32",
        "match_number": 8,
        "home_team": "H1",
        "away_team": "G2",
        "home_score": 1,
        "away_score": 0,
        "kickoff_time": "2026-07-01T20:00:00Z",
    },
    {
        "match_id": "R32-9",
        "round": "R32",
        "match_number": 9,
        "home_team": "I1",
        "away_team": "J2",
        "home_score": 3,
        "away_score": 2,
        "kickoff_time": "2026-07-02T16:00:00Z",
    },
    {
        "match_id": "R32-10",
        "round": "R32",
        "match_number": 10,
        "home_team": "K1",
        "away_team": "L2",
        "home_score": 2,
        "away_score": 1,
        "kickoff_time": "2026-07-02T20:00:00Z",
    },
    {
        "match_id": "R32-11",
        "round": "R32",
        "match_number": 11,
        "home_team": "M1",
        "away_team": "N2",
        "home_score": 1,
        "away_score": 0,
        "kickoff_time": "2026-07-03T16:00:00Z",
    },
    {
        "match_id": "R32-12",
        "round": "R32",
        "match_number": 12,
        "home_team": "O1",
        "away_team": "P2",
        "home_score": 2,
        "away_score": 0,
        "kickoff_time": "2026-07-03T20:00:00Z",
    },
    {
        "match_id": "R32-13",
        "round": "R32",
        "match_number": 13,
        "home_team": "J1",
        "away_team": "I2",
        "home_score": 1,
        "away_score": 0,
        "kickoff_time": "2026-07-04T16:00:00Z",
    },
    {
        "match_id": "R32-14",
        "round": "R32",
        "match_number": 14,
        "home_team": "L1",
        "away_team": "K2",
        "home_score": 2,
        "away_score": 0,
        "kickoff_time": "2026-07-04T20:00:00Z",
    },
    {
        "match_id": "R32-15",
        "round": "R32",
        "match_number": 15,
        "home_team": "N1",
        "away_team": "M2",
        "home_score": 3,
        "away_score": 1,
        "kickoff_time": "2026-07-05T16:00:00Z",
    },
    {
        "match_id": "R32-16",
        "round": "R32",
        "match_number": 16,
        "home_team": "P1",
        "away_team": "O2",
        "home_score": 2,
        "away_score": 1,
        "kickoff_time": "2026-07-05T20:00:00Z",
    },
    # ── R16 ───────────────────────────────────────────────────────────────────
    {
        "match_id": "R16-1",
        "round": "R16",
        "match_number": 1,
        "home_team": "A1",
        "away_team": "G1",
        "home_score": 2,
        "away_score": 0,
        "kickoff_time": "2026-07-06T16:00:00Z",
    },
    {
        "match_id": "R16-2",
        "round": "R16",
        "match_number": 2,
        "home_team": "E1",
        "away_team": "D1",
        "home_score": 1,
        "away_score": 0,
        "kickoff_time": "2026-07-06T20:00:00Z",
    },
    {
        "match_id": "R16-3",
        "round": "R16",
        "match_number": 3,
        "home_team": "C1",
        "away_team": "B1",
        "home_score": 3,
        "away_score": 1,
        "kickoff_time": "2026-07-07T16:00:00Z",
    },
    {
        "match_id": "R16-4",
        "round": "R16",
        "match_number": 4,
        "home_team": "F1",
        "away_team": "H1",
        "home_score": 0,
        "away_score": 1,
        "kickoff_time": "2026-07-07T20:00:00Z",
    },
    {
        "match_id": "R16-5",
        "round": "R16",
        "match_number": 5,
        "home_team": "O1",
        "away_team": "M1",
        "home_score": 2,
        "away_score": 1,
        "kickoff_time": "2026-07-08T16:00:00Z",
    },
    {
        "match_id": "R16-6",
        "round": "R16",
        "match_number": 6,
        "home_team": "K1",
        "away_team": "I1",
        "home_score": 1,
        "away_score": 0,
        "kickoff_time": "2026-07-08T20:00:00Z",
    },
    {
        "match_id": "R16-7",
        "round": "R16",
        "match_number": 7,
        "home_team": "N1",
        "away_team": "L1",
        "home_score": 2,
        "away_score": 0,
        "kickoff_time": "2026-07-09T16:00:00Z",
    },
    {
        "match_id": "R16-8",
        "round": "R16",
        "match_number": 8,
        "home_team": "J1",
        "away_team": "P1",
        "home_score": 1,
        "away_score": 0,
        "kickoff_time": "2026-07-09T20:00:00Z",
    },
    # ── QF ────────────────────────────────────────────────────────────────────
    {
        "match_id": "QF-1",
        "round": "QF",
        "match_number": 1,
        "home_team": "A1",
        "away_team": "E1",
        "home_score": 3,
        "away_score": 1,
        "kickoff_time": "2026-07-10T16:00:00Z",
    },
    {
        "match_id": "QF-2",
        "round": "QF",
        "match_number": 2,
        "home_team": "O1",
        "away_team": "K1",
        "home_score": 2,
        "away_score": 0,
        "kickoff_time": "2026-07-10T20:00:00Z",
    },
    {
        "match_id": "QF-3",
        "round": "QF",
        "match_number": 3,
        "home_team": "C1",
        "away_team": "H1",
        "home_score": 2,
        "away_score": 1,
        "kickoff_time": "2026-07-11T16:00:00Z",
    },
    {
        "match_id": "QF-4",
        "round": "QF",
        "match_number": 4,
        "home_team": "N1",
        "away_team": "J1",
        "home_score": 2,
        "away_score": 1,
        "kickoff_time": "2026-07-11T20:00:00Z",
    },
    # ── SF (score-bearing) ────────────────────────────────────────────────────
    {
        "match_id": "SF-1",
        "round": "SF",
        "match_number": 1,
        "home_team": "A1",
        "away_team": "O1",
        "home_score": 1,
        "away_score": 1,
        "pk_home_score": 4,
        "pk_away_score": 3,
        "pk_winner": "A1",
        "kickoff_time": "2026-07-13T20:00:00Z",
    },
    {
        "match_id": "SF-2",
        "round": "SF",
        "match_number": 2,
        "home_team": "C1",
        "away_team": "N1",
        "home_score": 2,
        "away_score": 0,
        "kickoff_time": "2026-07-14T20:00:00Z",
    },
    # ── FINAL + TP (score-bearing) ────────────────────────────────────────────
    {
        "match_id": "FINAL",
        "round": "FINAL",
        "match_number": 1,
        "home_team": "A1",
        "away_team": "C1",
        "home_score": 2,
        "away_score": 1,
        "kickoff_time": "2026-07-19T20:00:00Z",
    },
    {
        "match_id": "TP",
        "round": "TP",
        "match_number": 1,
        "home_team": "O1",
        "away_team": "N1",
        "home_score": 3,
        "away_score": 0,
        "kickoff_time": "2026-07-19T16:00:00Z",
    },
]


def simulate():
    for result in RESULTS:
        match_id = result["match_id"]
        result["status"] = "completed"
        table.put_item(Item=result)

        winner = result.get("pk_winner")
        if not winner:
            winner = (
                result["home_team"]
                if result["home_score"] > result["away_score"]
                else result["away_team"]
            )
        score_line = f"{result['home_score']}-{result['away_score']}"
        if result.get("pk_home_score") is not None:
            score_line += f" (PK {result['pk_home_score']}-{result['pk_away_score']})"

        print(
            f"{match_id:8s}  {result['home_team']:3s} vs {result['away_team']:3s}  {score_line:16s}  → {winner}"
        )

    print(
        f"\nAll {len(RESULTS)} matches completed. Refresh /bracket to see the full tournament."
    )


if __name__ == "__main__":
    simulate()

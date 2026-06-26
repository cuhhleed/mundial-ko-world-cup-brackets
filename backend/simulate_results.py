"""
Simulate match results for testing the bracket viewer.

Updates scheduled R32 matches to completed with specific results.
Run AFTER seeding and creating a bracket so the results appear as
post-submission outcomes (not locked slots).

Usage:
    python simulate_results.py
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

RESULTS = [
    # R32-3: home team wins 2-0 (user likely predicted E1 or F2 — tests correct/incorrect winner)
    {
        "match_id": "R32-3",
        "home_score": 2,
        "away_score": 0,
        "winner_note": "E1 wins 2-0",
    },
    # R32-4: away team wins 1-0 (tests incorrect winner if user picked G1)
    {
        "match_id": "R32-4",
        "home_score": 0,
        "away_score": 1,
        "winner_note": "H2 wins 1-0",
    },
    # R32-5: draw, goes to PK — home team wins on pens
    {
        "match_id": "R32-5",
        "home_score": 1,
        "away_score": 1,
        "pk_home_score": 5,
        "pk_away_score": 4,
        "pk_winner": "B1",
        "winner_note": "B1 wins on penalties 5-4",
    },
    # R32-6: home team wins 3-1 (tests score comparison)
    {
        "match_id": "R32-6",
        "home_score": 3,
        "away_score": 1,
        "winner_note": "D1 wins 3-1",
    },
]


def simulate():
    for result in RESULTS:
        match_id = result["match_id"]
        note = result.pop("winner_note")

        update_expr = "SET #s = :status, home_score = :hs, away_score = :as_"
        expr_values: dict = {
            ":status": "completed",
            ":hs": result["home_score"],
            ":as_": result["away_score"],
        }
        expr_names = {"#s": "status"}

        if "pk_home_score" in result:
            update_expr += (
                ", pk_home_score = :pkh, pk_away_score = :pka, pk_winner = :pkw"
            )
            expr_values[":pkh"] = result["pk_home_score"]
            expr_values[":pka"] = result["pk_away_score"]
            expr_values[":pkw"] = result["pk_winner"]

        table.update_item(
            Key={"match_id": match_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values,
        )
        print(f"Completed {match_id}: {note}")

    print("\nDone. Refresh /bracket to see accuracy indicators.")


if __name__ == "__main__":
    simulate()

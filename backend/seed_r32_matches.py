import os

import boto3

PROJECT_NAME = os.getenv("PROJECT_NAME", "mundial-ko")
ENVIRONMENT = os.getenv("ENVIRONMENT", "local")

R32_TEAMS: dict[str, tuple[str, str]] = {
    "R32-1": ("A1", "B2"),
    "R32-2": ("C1", "D2"),
    "R32-3": ("E1", "F2"),
    "R32-4": ("G1", "H2"),
    "R32-5": ("B1", "A2"),
    "R32-6": ("D1", "C2"),
    "R32-7": ("F1", "E2"),
    "R32-8": ("H1", "G2"),
    "R32-9": ("I1", "J2"),
    "R32-10": ("K1", "L2"),
    "R32-11": ("M1", "N2"),
    "R32-12": ("O1", "P2"),
    "R32-13": ("J1", "I2"),
    "R32-14": ("L1", "K2"),
    "R32-15": ("N1", "M2"),
    "R32-16": ("P1", "O2"),
}


def seed_matches():
    table_name = f"{PROJECT_NAME}-{ENVIRONMENT}-matches"
    table = boto3.resource(
        "dynamodb",
        endpoint_url=os.getenv("DYNAMODB_ENDPOINT_URL", "http://localhost:8001"),
        region_name="localhost",
        aws_access_key_id="DUMMYIDEXAMPLE",
        aws_secret_access_key="DUMMYSECRETANDKEYEXAMPLE",
    ).Table(table_name)

    for slot_id, (home, away) in R32_TEAMS.items():
        table.put_item(
            Item={
                "match_id": slot_id,
                "round": "R32",
                "match_number": int(slot_id.split("-")[1]),
                "home_team": home,
                "away_team": away,
                "status": "scheduled",
                "kickoff_time": "2026-06-29T16:00:00Z",
            }
        )
        print(f"Seeded scheduled match: {slot_id}", flush=True)

    print("Match seeding complete.\n", flush=True)


if __name__ == "__main__":
    seed_matches()

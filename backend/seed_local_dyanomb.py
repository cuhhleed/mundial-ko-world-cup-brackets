import os

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

PROJECT_NAME = os.getenv("PROJECT_NAME", "mundial-ko")
ENVIRONMENT = os.getenv("ENVIRONMENT", "local")

fast_config = Config(connect_timeout=5, read_timeout=5, retries={"max_attempts": 1})

dynamodb = boto3.client(
    "dynamodb",
    endpoint_url=os.getenv("DYNAMODB_ENDPOINT_URL", "http://localhost:8001"),
    region_name="localhost",
    aws_access_key_id="DUMMYIDEXAMPLE",
    aws_secret_access_key="DUMMYSECRETANDKEYEXAMPLE",
    config=fast_config,
)

TABLES_SCHEMA = [
    {
        "TableName": f"{PROJECT_NAME}-{ENVIRONMENT}-users",
        "KeySchema": [{"AttributeName": "user_id", "KeyType": "HASH"}],
        "AttributeDefinitions": [
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "email", "AttributeType": "S"},
        ],
        "GlobalSecondaryIndexes": [
            {
                "IndexName": "email-index",
                "KeySchema": [{"AttributeName": "email", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "KEYS_ONLY"},
            }
        ],
    },
    {
        "TableName": f"{PROJECT_NAME}-{ENVIRONMENT}-brackets",
        "KeySchema": [{"AttributeName": "bracket_id", "KeyType": "HASH"}],
        "AttributeDefinitions": [
            {"AttributeName": "bracket_id", "AttributeType": "S"},
            {"AttributeName": "user_id", "AttributeType": "S"},
        ],
        "GlobalSecondaryIndexes": [
            {
                "IndexName": "user_id-index",
                "KeySchema": [{"AttributeName": "user_id", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
    },
    {
        "TableName": f"{PROJECT_NAME}-{ENVIRONMENT}-matches",
        "KeySchema": [{"AttributeName": "match_id", "KeyType": "HASH"}],
        "AttributeDefinitions": [
            {"AttributeName": "match_id", "AttributeType": "S"},
            {"AttributeName": "round", "AttributeType": "S"},
        ],
        "GlobalSecondaryIndexes": [
            {
                "IndexName": "round-index",
                "KeySchema": [{"AttributeName": "round", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
    },
]


def init_tables():
    for schema in TABLES_SCHEMA:
        name = schema["TableName"]
        print(f"Creating table '{name}'...", flush=True)

        create_kwargs = {
            "TableName": name,
            "KeySchema": schema["KeySchema"],
            "AttributeDefinitions": schema["AttributeDefinitions"],
            "BillingMode": "PAY_PER_REQUEST",
        }

        if "GlobalSecondaryIndexes" in schema:
            create_kwargs["GlobalSecondaryIndexes"] = schema["GlobalSecondaryIndexes"]

        try:
            dynamodb.create_table(**create_kwargs)
            print(f"✅ Table '{name}' created successfully.\n", flush=True)

        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceInUseException":
                print(f"ℹ️ Table '{name}' already exists. Skipping.\n", flush=True)
            else:
                print(f"❌ Failed to create table '{name}': {e}\n", flush=True)


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

COMPLETED_MATCHES = [
    {
        "match_id": "R32-1",
        "round": "R32",
        "match_number": 1,
        "home_team": "A1",
        "away_team": "B2",
        "home_score": 2,
        "away_score": 1,
        "status": "completed",
        "kickoff_time": "2026-06-28T16:00:00Z",
    },
    {
        "match_id": "R32-2",
        "round": "R32",
        "match_number": 2,
        "home_team": "C1",
        "away_team": "D2",
        "home_score": 0,
        "away_score": 0,
        "pk_home_score": 4,
        "pk_away_score": 3,
        "pk_winner": "C1",
        "status": "completed",
        "kickoff_time": "2026-06-28T20:00:00Z",
    },
]


def seed_matches():
    table_name = f"{PROJECT_NAME}-{ENVIRONMENT}-matches"
    table = boto3.resource(
        "dynamodb",
        endpoint_url=os.getenv("DYNAMODB_ENDPOINT_URL", "http://localhost:8001"),
        region_name="localhost",
        aws_access_key_id="DUMMYIDEXAMPLE",
        aws_secret_access_key="DUMMYSECRETANDKEYEXAMPLE",
    ).Table(table_name)

    for match in COMPLETED_MATCHES:
        table.put_item(Item=match)
        print(f"Seeded completed match: {match['match_id']}", flush=True)

    completed_ids = {m["match_id"] for m in COMPLETED_MATCHES}
    for slot_id, (home, away) in R32_TEAMS.items():
        if slot_id in completed_ids:
            continue
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
    init_tables()
    seed_matches()

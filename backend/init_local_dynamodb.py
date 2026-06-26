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


if __name__ == "__main__":
    init_tables()

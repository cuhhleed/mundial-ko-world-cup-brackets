import boto3

from app.config import settings

_resource = None


def get_dynamodb():
    global _resource
    if _resource is None:
        kwargs = {"region_name": settings.AWS_REGION}

        # Local only: point at dynamodb-local with the dummy static creds. In a
        # deployed environment there is no endpoint URL, so we pass no explicit
        # credentials and boto3 resolves the ECS task role via its default chain
        # (passing the dummy creds here would override the task role and get
        # rejected by real DynamoDB as UnrecognizedClientException).
        if settings.DYNAMODB_ENDPOINT_URL:
            kwargs["endpoint_url"] = settings.DYNAMODB_ENDPOINT_URL
            kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
            kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY

        _resource = boto3.resource("dynamodb", **kwargs)
    return _resource


def get_table(name: str):
    return get_dynamodb().Table(name)

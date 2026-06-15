import boto3

from app.config import settings

_resource = None


def get_dynamodb():
    global _resource
    if _resource is None:
        kwargs = {"region_name": settings.AWS_REGION}
        if settings.DYNAMODB_ENDPOINT_URL:
            kwargs["endpoint_url"] = settings.DYNAMODB_ENDPOINT_URL
        _resource = boto3.resource("dynamodb", **kwargs)
    return _resource


def get_table(name: str):
    return get_dynamodb().Table(name)

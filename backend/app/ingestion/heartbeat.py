import boto3

from app.config import settings
from app.logging import get_logger

logger = get_logger("heartbeat")

_cloudwatch = boto3.client("cloudwatch", region_name=settings.AWS_REGION)


def emit_heartbeat() -> None:
    """Publish a single IngestionHeartbeat metric data point to CloudWatch."""
    _cloudwatch.put_metric_data(
        Namespace=settings.CLOUDWATCH_NAMESPACE,
        MetricData=[
            {
                "MetricName": "IngestionHeartbeat",
                "Dimensions": [
                    {
                        "Name": "Environment",
                        "Value": settings.ENVIRONMENT,
                    }
                ],
                "Value": 1,
                "Unit": "Count",
            }
        ],
    )
    logger.info("heartbeat_emitted", namespace=settings.CLOUDWATCH_NAMESPACE)

resource "aws_sns_topic" "ingestion_alarm" {
  name = "${var.project_name}-${var.environment}-ingestion-alarm"

  tags = {
    Name = "${var.project_name}-${var.environment}-ingestion-alarm"
  }
}

resource "aws_sns_topic_subscription" "ingestion_alarm_email" {
  topic_arn = aws_sns_topic.ingestion_alarm.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

resource "aws_cloudwatch_metric_alarm" "ingestion_heartbeat" {
  alarm_name          = "${var.project_name}-${var.environment}-ingestion-heartbeat"
  alarm_description   = "Fires when the ingestion service stops emitting heartbeat metrics"
  namespace           = "MundialKO"
  metric_name         = "IngestionHeartbeat"
  statistic           = "Sum"
  period              = 3600
  evaluation_periods  = 2
  comparison_operator = "LessThanThreshold"
  threshold           = 1
  treat_missing_data  = "breaching"

  dimensions = {
    Environment = var.environment
  }

  alarm_actions = [aws_sns_topic.ingestion_alarm.arn]

  tags = {
    Name = "${var.project_name}-${var.environment}-ingestion-heartbeat-alarm"
  }
}

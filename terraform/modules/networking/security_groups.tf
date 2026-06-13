# ---------------------------------------------------------------------------
# Security Group shells
# All ingress/egress rules use standalone rule resources so that SGs that
# reference each other can be declared without circular dependencies.
# ---------------------------------------------------------------------------

resource "aws_security_group" "alb" {
  name        = "${var.project_name}-${var.environment}-alb-sg"
  description = "ALB accepts HTTP/HTTPS from the internet, forwards to ECS"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-${var.environment}-alb-sg"
  }

  # Lifecycle block prevents Terraform from deleting the SG before
  # dependent rule resources are destroyed.
  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_security_group" "ecs" {
  name        = "${var.project_name}-${var.environment}-ecs-sg"
  description = "ECS Fargate tasks accepts traffic from ALB only"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-${var.environment}-ecs-sg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_security_group" "elasticache" {
  name        = "${var.project_name}-${var.environment}-elasticache-sg"
  description = "ElastiCache Redis accepts traffic from ECS tasks only"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-${var.environment}-elasticache-sg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# ---------------------------------------------------------------------------
# ALB ingress rules
# ---------------------------------------------------------------------------

resource "aws_vpc_security_group_ingress_rule" "alb_http" {
  security_group_id = aws_security_group.alb.id
  description       = "Allow HTTP from anywhere"
  ip_protocol       = "tcp"
  from_port         = 80
  to_port           = 80
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_vpc_security_group_ingress_rule" "alb_https" {
  security_group_id = aws_security_group.alb.id
  description       = "Allow HTTPS from anywhere"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
  cidr_ipv4         = "0.0.0.0/0"
}

# ---------------------------------------------------------------------------
# ALB egress rules
# ---------------------------------------------------------------------------

resource "aws_vpc_security_group_egress_rule" "alb_to_ecs" {
  security_group_id            = aws_security_group.alb.id
  description                  = "Allow ALB to forward to ECS container port"
  ip_protocol                  = "tcp"
  from_port                    = var.container_port
  to_port                      = var.container_port
  referenced_security_group_id = aws_security_group.ecs.id
}

# ---------------------------------------------------------------------------
# ECS ingress rules
# ---------------------------------------------------------------------------

resource "aws_vpc_security_group_ingress_rule" "ecs_from_alb" {
  security_group_id            = aws_security_group.ecs.id
  description                  = "Allow traffic from ALB on container port"
  ip_protocol                  = "tcp"
  from_port                    = var.container_port
  to_port                      = var.container_port
  referenced_security_group_id = aws_security_group.alb.id
}

# ---------------------------------------------------------------------------
# ECS egress rules
# ---------------------------------------------------------------------------

resource "aws_vpc_security_group_egress_rule" "ecs_all_outbound" {
  security_group_id = aws_security_group.ecs.id
  description       = "Allow all outbound traffic from ECS tasks"
  ip_protocol       = "-1"
  cidr_ipv4         = "0.0.0.0/0"
}

# ---------------------------------------------------------------------------
# ElastiCache ingress rules
# ---------------------------------------------------------------------------

resource "aws_vpc_security_group_ingress_rule" "elasticache_from_ecs" {
  security_group_id            = aws_security_group.elasticache.id
  description                  = "Allow Redis traffic from ECS tasks only"
  ip_protocol                  = "tcp"
  from_port                    = 6379
  to_port                      = 6379
  referenced_security_group_id = aws_security_group.ecs.id
}

# ---------------------------------------------------------------------------
# ElastiCache egress rules
# ---------------------------------------------------------------------------

resource "aws_vpc_security_group_egress_rule" "elasticache_to_ecs" {
  security_group_id            = aws_security_group.elasticache.id
  description                  = "Allow responses back to ECS tasks"
  ip_protocol                  = "tcp"
  from_port                    = 1024
  to_port                      = 65535
  referenced_security_group_id = aws_security_group.ecs.id
}

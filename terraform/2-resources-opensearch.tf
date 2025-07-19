# Security Group for OpenSearch
resource "aws_security_group" "opensearch" {
  name        = "${local.name_prefix}-opensearch-sg"
  description = "Security group for OpenSearch cluster"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.lambda.id]
  }

  ingress {
    from_port       = 9200
    to_port         = 9200
    protocol        = "tcp"
    security_groups = [aws_security_group.lambda.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-opensearch-sg"
  })
}

# OpenSearch Domain
resource "aws_opensearch_domain" "main" {
  domain_name    = local.opensearch_domain_name
  engine_version = "OpenSearch_2.11"

  cluster_config {
    instance_type            = var.opensearch_instance_type
    instance_count           = var.opensearch_instance_count
    dedicated_master_enabled = false
    zone_awareness_enabled   = var.opensearch_instance_count > 1
    
    dynamic "zone_awareness_config" {
      for_each = var.opensearch_instance_count > 1 ? [1] : []
      content {
        availability_zone_count = min(var.opensearch_instance_count, 2)
      }
    }
  }

  vpc_options {
    security_group_ids = [aws_security_group.opensearch.id]
    subnet_ids = var.opensearch_instance_count > 1 ? [
      aws_subnet.private[0].id,
      aws_subnet.private[1].id
    ] : [aws_subnet.private[0].id]
  }

  ebs_options {
    ebs_enabled = true
    volume_type = "gp3"
    volume_size = var.opensearch_volume_size
  }

  encrypt_at_rest {
    enabled = true
  }

  node_to_node_encryption {
    enabled = true
  }

  domain_endpoint_options {
    enforce_https       = true
    tls_security_policy = "Policy-Min-TLS-1-2-2019-07"
  }

  advanced_security_options {
    enabled                        = true
    anonymous_auth_enabled         = false
    internal_user_database_enabled = true
    
    master_user_options {
      master_user_name     = "admin"
      master_user_password = random_password.opensearch_password.result
    }
  }

  access_policies = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = "*"
        }
        Action   = "es:*"
        Resource = "arn:aws:es:${var.aws_region}:${data.aws_caller_identity.current.account_id}:domain/${local.opensearch_domain_name}/*"
      }
    ]
  })

  log_publishing_options {
    cloudwatch_log_group_arn = aws_cloudwatch_log_group.opensearch.arn
    log_type                 = "INDEX_SLOW_LOGS"
  }

  log_publishing_options {
    cloudwatch_log_group_arn = aws_cloudwatch_log_group.opensearch.arn
    log_type                 = "SEARCH_SLOW_LOGS"
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-opensearch-domain"
  })

  depends_on = [
    aws_iam_service_linked_role.opensearch,
    aws_cloudwatch_log_resource_policy.opensearch
  ]
}

# CloudWatch Log Group for OpenSearch
resource "aws_cloudwatch_log_group" "opensearch" {
  name              = "/aws/opensearch/domains/${local.name_prefix}-logs"
  retention_in_days = 7

  tags = local.common_tags
}

# CloudWatch Log Resource Policy for OpenSearch
resource "aws_cloudwatch_log_resource_policy" "opensearch" {
  policy_name = "${local.name_prefix}-opensearch-log-policy"

  policy_document = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "es.amazonaws.com"
        }
        Action = [
          "logs:PutLogEvents",
          "logs:CreateLogGroup",
          "logs:CreateLogStream"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:*"
      }
    ]
  })
}

# IAM Service Linked Role for OpenSearch
resource "aws_iam_service_linked_role" "opensearch" {
  aws_service_name = "opensearchservice.amazonaws.com"
  description      = "Service linked role for OpenSearch"
}

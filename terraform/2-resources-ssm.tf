# SSM Parameters for SAM consumption
resource "aws_ssm_parameter" "vpc_id" {
  name  = "/chatbot/${var.environment}/vpc/id"
  type  = "String"
  value = aws_vpc.main.id

  tags = local.common_tags
}

resource "aws_ssm_parameter" "subnet_ids" {
  name  = "/chatbot/${var.environment}/vpc/subnet_ids"
  type  = "StringList"
  value = join(",", aws_subnet.private[*].id)

  tags = local.common_tags
}

resource "aws_ssm_parameter" "subnet_id_1" {
  name  = "/chatbot/${var.environment}/vpc/subnet_id_1"
  type  = "String"
  value = aws_subnet.private[0].id

  tags = local.common_tags
}

resource "aws_ssm_parameter" "subnet_id_2" {
  name  = "/chatbot/${var.environment}/vpc/subnet_id_2"
  type  = "String"
  value = aws_subnet.private[1].id

  tags = local.common_tags
}

resource "aws_ssm_parameter" "security_group_id" {
  name  = "/chatbot/${var.environment}/vpc/security_group_id"
  type  = "String"
  value = aws_security_group.lambda.id

  tags = local.common_tags
}

resource "aws_ssm_parameter" "opensearch_endpoint" {
  name  = "/chatbot/${var.environment}/opensearch/endpoint"
  type  = "String"
  value = aws_opensearch_domain.main.endpoint

  tags = local.common_tags
}

resource "aws_ssm_parameter" "opensearch_username" {
  name  = "/chatbot/${var.environment}/opensearch/username"
  type  = "String"
  value = "admin"

  tags = local.common_tags
}

resource "aws_ssm_parameter" "documents_bucket_name" {
  name  = "/chatbot/${var.environment}/s3/documents_bucket"
  type  = "String"
  value = aws_s3_bucket.documents.id

  tags = local.common_tags
}

resource "aws_ssm_parameter" "lambda_code_bucket_name" {
  name  = "/chatbot/${var.environment}/s3/lambda_code_bucket"
  type  = "String"
  value = aws_s3_bucket.lambda_code.id

  tags = local.common_tags
}

# Secrets Manager for sensitive data
resource "aws_secretsmanager_secret" "opensearch_password" {
  name = "${var.project_name}-${var.environment}-opensearch-credentials"
  description = "OpenSearch master user password"

  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "opensearch_password" {
  secret_id = aws_secretsmanager_secret.opensearch_password.id
  secret_string = jsonencode({
    username = "admin"
    password = random_password.opensearch_password.result
  })
}

# Additional application parameters
resource "aws_ssm_parameter" "environment" {
  name  = "/chatbot/${var.environment}/app/environment"
  type  = "String"
  value = var.environment

  tags = local.common_tags
}

resource "aws_ssm_parameter" "project_name" {
  name  = "/chatbot/${var.environment}/app/project_name"
  type  = "String"
  value = var.project_name

  tags = local.common_tags
}

resource "aws_ssm_parameter" "aws_region" {
  name  = "/chatbot/${var.environment}/app/aws_region"
  type  = "String"
  value = var.aws_region

  tags = local.common_tags
}

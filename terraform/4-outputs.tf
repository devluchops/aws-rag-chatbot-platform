# VPC Outputs for SAM
output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = aws_subnet.private[*].id
}

output "security_group_id" {
  description = "ID of the default security group"
  value       = aws_security_group.lambda.id
}

# OpenSearch Outputs for SAM
output "opensearch_endpoint" {
  description = "OpenSearch domain endpoint"
  value       = aws_opensearch_domain.main.endpoint
}

output "opensearch_username" {
  description = "OpenSearch master username"
  value       = "admin"
}

output "opensearch_password" {
  description = "OpenSearch master password"
  value       = random_password.opensearch_password.result
  sensitive   = true
}

# S3 Outputs for SAM
output "documents_bucket_name" {
  description = "S3 bucket name for documents"
  value       = aws_s3_bucket.documents.id
}

output "lambda_code_bucket_name" {
  description = "S3 bucket name for Lambda code"
  value       = aws_s3_bucket.lambda_code.id
}

# SSM Parameter Names for SAM
output "ssm_parameter_prefix" {
  description = "SSM parameter prefix for SAM to consume"
  value       = "/${var.project_name}/${var.environment}"
}

output "opensearch_secret_name" {
  description = "Secrets Manager secret name for OpenSearch credentials"
  value       = aws_secretsmanager_secret.opensearch_password.name
}

# General Outputs
output "project_name" {
  description = "Name of the project"
  value       = var.project_name
}

output "environment" {
  description = "Environment name"
  value       = var.environment
}

output "aws_region" {
  description = "AWS region"
  value       = var.aws_region
}

output "random_suffix" {
  description = "Random suffix used for resource names"
  value       = random_string.suffix.result
}

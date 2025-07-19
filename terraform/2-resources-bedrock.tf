# Bedrock Model Access Configuration
# Note: Bedrock model access is managed at the account level, not per resource
#
# COST-OPTIMIZED MODELS USED IN THIS PROJECT:
# - amazon.titan-embed-text-v2 (embeddings) - ~$0.0001 per 1K tokens
# - anthropic.claude-3-haiku-20240307-v1:0 (text generation) - ~$0.00025 per 1K tokens
#
# TO REQUEST ACCESS:
# 1. Go to AWS Console -> Bedrock -> Model access
# 2. Request access to:
#    - Amazon Titan Text Embeddings V2
#    - Claude 3 Haiku
# 3. Wait for approval (usually instant for these models)

# Data source to check available foundation models
data "aws_bedrock_foundation_models" "available" {
  by_provider = "anthropic"
}

# Data source for Amazon Titan models
data "aws_bedrock_foundation_models" "titan" {
  by_provider = "amazon"
}

# Bedrock model invocation logging configuration (optional)
resource "aws_bedrock_model_invocation_logging_configuration" "chatbot_logging" {
  count = var.enable_bedrock_logging ? 1 : 0
  
  logging_config {
    cloudwatch_config {
      log_group_name = aws_cloudwatch_log_group.bedrock_logs[0].name
      role_arn      = aws_iam_role.bedrock_logging_role[0].arn
    }
    
    embedding_data_delivery_enabled = true
    image_data_delivery_enabled     = true
    text_data_delivery_enabled      = true
  }
}

# CloudWatch log group for Bedrock (optional)
resource "aws_cloudwatch_log_group" "bedrock_logs" {
  count = var.enable_bedrock_logging ? 1 : 0
  
  name              = "/aws/bedrock/${var.project_name}-${var.environment}"
  retention_in_days = 30
  
  tags = {
    Name        = "${var.project_name}-${var.environment}-bedrock-logs"
    Environment = var.environment
    Project     = var.project_name
  }
}

# IAM role for Bedrock logging (optional)
resource "aws_iam_role" "bedrock_logging_role" {
  count = var.enable_bedrock_logging ? 1 : 0
  
  name = "${var.project_name}-${var.environment}-bedrock-logging-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "bedrock.amazonaws.com"
        }
      }
    ]
  })
  
  tags = {
    Name        = "${var.project_name}-${var.environment}-bedrock-logging-role"
    Environment = var.environment
    Project     = var.project_name
  }
}

# IAM policy for Bedrock logging (optional)
resource "aws_iam_role_policy" "bedrock_logging_policy" {
  count = var.enable_bedrock_logging ? 1 : 0
  
  name = "${var.project_name}-${var.environment}-bedrock-logging-policy"
  role = aws_iam_role.bedrock_logging_role[0].id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/bedrock/${var.project_name}-${var.environment}:*"
      }
    ]
  })
}

# Output information about available models
output "available_anthropic_models" {
  description = "Available Anthropic models in Bedrock"
  value       = data.aws_bedrock_foundation_models.available.model_summaries
}

output "available_titan_models" {
  description = "Available Amazon Titan models in Bedrock"
  value       = data.aws_bedrock_foundation_models.titan.model_summaries
}

# Note: Model access requests need to be made through the AWS Console or CLI
# Run this command to request access to models:
# aws bedrock put-model-invocation-logging-configuration --region us-east-1

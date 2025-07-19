# Data sources
data "aws_caller_identity" "current" {}

data "aws_availability_zones" "available" {
  state = "available"
}

# Random suffix for unique resource names
resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

# Random password for OpenSearch
resource "random_password" "opensearch_password" {
  length  = 16
  special = true
}

# Local values
locals {
  name_prefix = "${var.project_name}-${var.environment}"
  # OpenSearch domain name (max 28 chars, lowercase, no underscores)
  opensearch_domain_name = lower(replace(substr("chatbot-${var.environment}-${random_string.suffix.result}", 0, 28), "_", "-"))
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

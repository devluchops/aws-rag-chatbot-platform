# S3 Bucket for documents
resource "aws_s3_bucket" "documents" {
  bucket = "${local.name_prefix}-documents-${random_string.suffix.result}"

  tags = merge(local.common_tags, {
    Name        = "${local.name_prefix}-documents-bucket"
    Description = "S3 bucket for storing documents"
  })
}

resource "aws_s3_bucket_versioning" "documents" {
  bucket = aws_s3_bucket.documents.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "documents" {
  bucket = aws_s3_bucket.documents.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "documents" {
  bucket = aws_s3_bucket.documents.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "documents" {
  bucket = aws_s3_bucket.documents.id

  rule {
    id     = "transition_to_ia"
    status = "Enabled"

    filter {}

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }
  }
}

# S3 Bucket for Lambda deployment packages
resource "aws_s3_bucket" "lambda_code" {
  bucket = "${local.name_prefix}-lambda-code-${random_string.suffix.result}"

  tags = merge(local.common_tags, {
    Name        = "${local.name_prefix}-lambda-code-bucket"
    Description = "S3 bucket for Lambda deployment packages"
  })
}

resource "aws_s3_bucket_versioning" "lambda_code" {
  bucket = aws_s3_bucket.lambda_code.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "lambda_code" {
  bucket = aws_s3_bucket.lambda_code.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "lambda_code" {
  bucket = aws_s3_bucket.lambda_code.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "lambda_code" {
  bucket = aws_s3_bucket.lambda_code.id

  rule {
    id     = "cleanup_old_versions"
    status = "Enabled"

    filter {}

    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }
}

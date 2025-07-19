#!/bin/bash

# Simple AWS S3 Bucket Cleanup Script
# This script empties S3 buckets to allow Terraform destroy to complete

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default configuration (can be overridden by environment variables or .env file)
PROJECT_NAME=${PROJECT_NAME:-"aws-chatbot"}
ENVIRONMENT=${ENVIRONMENT:-${ENV:-"dev"}}  # Support both ENVIRONMENT and ENV variables

# Function to load configuration
load_config() {
    # Try to load from .env file in project root
    if [ -f "$(dirname "$0")/../.env" ]; then
        echo -e "${YELLOW}Loading configuration from .env file...${NC}"
        source "$(dirname "$0")/../.env"
        # Handle both ENV and ENVIRONMENT variables
        if [ -n "$ENV" ] && [ -z "$ENVIRONMENT" ]; then
            ENVIRONMENT="$ENV"
        fi
    fi
    
    # Try to load from terraform variables
    if [ -f "$(dirname "$0")/../terraform/environments/${ENVIRONMENT}.tfvars" ]; then
        echo -e "${YELLOW}Loading configuration from terraform/${ENVIRONMENT}.tfvars...${NC}"
        # Parse terraform variables
        while IFS= read -r line; do
            if [[ $line =~ ^project_name[[:space:]]*=[[:space:]]*\"(.*)\" ]]; then
                PROJECT_NAME="${BASH_REMATCH[1]}"
            elif [[ $line =~ ^environment[[:space:]]*=[[:space:]]*\"(.*)\" ]]; then
                ENVIRONMENT="${BASH_REMATCH[1]}"
            fi
        done < "$(dirname "$0")/../terraform/environments/${ENVIRONMENT}.tfvars"
    fi
    
    # Create the bucket name pattern
    BUCKET_PREFIX="${PROJECT_NAME}-${ENVIRONMENT}"
    
    echo -e "${GREEN}Configuration loaded:${NC}"
    echo "  Project: $PROJECT_NAME"
    echo "  Environment: $ENVIRONMENT"
    echo "  Bucket prefix: $BUCKET_PREFIX"
}

echo -e "${GREEN}Starting S3 bucket cleanup for ${PROJECT_NAME}-${ENVIRONMENT}...${NC}"

# Load configuration
load_config

# Function to empty a bucket
empty_bucket() {
    local bucket_name=$1
    
    if [ -z "$bucket_name" ]; then
        return
    fi
    
    # Safety check: Only allow buckets with specific patterns based on configuration
    if [[ ! "$bucket_name" =~ ^${BUCKET_PREFIX}-(documents|lambda-code)- ]]; then
        echo -e "${RED}SAFETY CHECK FAILED: $bucket_name does not match expected pattern${NC}"
        echo -e "${RED}Expected pattern: ${BUCKET_PREFIX}-(documents|lambda-code)-*${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}Processing bucket: $bucket_name${NC}"
    
    # Check if bucket exists
    if ! aws s3api head-bucket --bucket "$bucket_name" 2>/dev/null; then
        echo -e "${RED}Bucket $bucket_name not found or not accessible${NC}"
        return
    fi
    
    echo "Removing all objects and versions from $bucket_name..."
    
    # Remove all current objects
    aws s3 rm "s3://$bucket_name" --recursive --quiet 2>/dev/null || true
    
    # Handle versioned objects using a different approach
    echo "Checking for versioned objects..."
    
    # List and delete all versions (including delete markers)
    aws s3api list-object-versions --bucket "$bucket_name" --output text --query 'Versions[].{Key:Key,VersionId:VersionId}' 2>/dev/null | \
    while read key version_id; do
        if [ -n "$key" ] && [ -n "$version_id" ] && [ "$key" != "None" ] && [ "$version_id" != "None" ]; then
            aws s3api delete-object --bucket "$bucket_name" --key "$key" --version-id "$version_id" >/dev/null 2>&1 || true
        fi
    done
    
    # List and delete all delete markers
    aws s3api list-object-versions --bucket "$bucket_name" --output text --query 'DeleteMarkers[].{Key:Key,VersionId:VersionId}' 2>/dev/null | \
    while read key version_id; do
        if [ -n "$key" ] && [ -n "$version_id" ] && [ "$key" != "None" ] && [ "$version_id" != "None" ]; then
            aws s3api delete-object --bucket "$bucket_name" --key "$key" --version-id "$version_id" >/dev/null 2>&1 || true
        fi
    done
    
    echo -e "${GREEN}✓ Bucket $bucket_name has been emptied${NC}"
}

# Find and clean ONLY the specific project buckets
echo "Searching for SPECIFIC ${BUCKET_PREFIX} project buckets..."

# Get ONLY the specific buckets for this project (documents and lambda-code)
DOCUMENTS_BUCKET=$(aws s3api list-buckets --query "Buckets[?contains(Name, \`${BUCKET_PREFIX}-documents\`)].Name" --output text 2>/dev/null || echo "")
LAMBDA_CODE_BUCKET=$(aws s3api list-buckets --query "Buckets[?contains(Name, \`${BUCKET_PREFIX}-lambda-code\`)].Name" --output text 2>/dev/null || echo "")

# Create array of buckets to clean (only the ones we know should exist)
BUCKETS_TO_CLEAN=()

if [ -n "$DOCUMENTS_BUCKET" ] && [ "$DOCUMENTS_BUCKET" != "None" ]; then
    BUCKETS_TO_CLEAN+=("$DOCUMENTS_BUCKET")
fi

if [ -n "$LAMBDA_CODE_BUCKET" ] && [ "$LAMBDA_CODE_BUCKET" != "None" ]; then
    BUCKETS_TO_CLEAN+=("$LAMBDA_CODE_BUCKET")
fi

if [ ${#BUCKETS_TO_CLEAN[@]} -eq 0 ]; then
    echo -e "${YELLOW}No project buckets found. Checking what buckets exist...${NC}"
    echo "All your S3 buckets:"
    aws s3 ls
    echo ""
    echo -e "${RED}ERROR: Could not find the expected buckets:${NC}"
    echo "  - ${BUCKET_PREFIX}-documents-*"
    echo "  - ${BUCKET_PREFIX}-lambda-code-*"
    echo ""
    echo "Please verify the bucket names match the pattern above."
    echo "Current configuration: PROJECT_NAME=$PROJECT_NAME, ENVIRONMENT=$ENVIRONMENT"
    exit 1
fi

echo -e "${GREEN}Found PROJECT SPECIFIC buckets to clean:${NC}"
for bucket in "${BUCKETS_TO_CLEAN[@]}"; do
    echo "  - $bucket"
done

echo ""
echo -e "${YELLOW}Configuration being used:${NC}"
echo "  Project: $PROJECT_NAME"
echo "  Environment: $ENVIRONMENT"
echo "  Bucket prefix: $BUCKET_PREFIX"
echo ""
read -p "Are you sure you want to empty these buckets? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Operation cancelled."
    echo ""
    echo -e "${YELLOW}To configure different settings:${NC}"
    echo "1. Copy .env.example to .env and modify the values"
    echo "2. Or set environment variables: PROJECT_NAME=your-project ENVIRONMENT=your-env"
    echo "3. Or modify terraform/environments/\${ENVIRONMENT}.tfvars"
    exit 0
fi

echo "Starting cleanup of PROJECT SPECIFIC buckets..."

for bucket in "${BUCKETS_TO_CLEAN[@]}"; do
    empty_bucket "$bucket"
done

echo ""
echo -e "${GREEN}✓ S3 cleanup completed!${NC}"
echo -e "${YELLOW}Now you can run 'terraform destroy' to remove the infrastructure${NC}"

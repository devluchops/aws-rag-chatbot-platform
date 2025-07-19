#!/bin/bash

# Upload sample documents to the chatbot
set -e

echo "📚 Uploading sample documents to AWS RAG Chatbot..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Set variables
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.."
DATA_DIR="$PROJECT_DIR/data"
TERRAFORM_DIR="$PROJECT_DIR/terraform"

# Check if terraform output is available
if [ ! -d "$TERRAFORM_DIR" ]; then
    echo -e "${RED}Terraform directory not found. Please run deploy.sh first.${NC}"
    exit 1
fi

cd "$TERRAFORM_DIR"

# Get API Gateway URL
API_GATEWAY_URL=$(terraform output -raw api_gateway_url 2>/dev/null || echo "")

if [ -z "$API_GATEWAY_URL" ]; then
    echo -e "${RED}API Gateway URL not found. Please run deploy.sh first.${NC}"
    exit 1
fi

echo "🔗 Using API Gateway URL: $API_GATEWAY_URL"

# Function to upload a document
upload_document() {
    local file_path="$1"
    local title="$2"
    
    echo "  📄 Uploading: $title"
    
    # Read file content
    content=$(cat "$file_path")
    
    # Create JSON payload
    json_payload=$(jq -n \
        --arg title "$title" \
        --arg content "$content" \
        '{
            "title": $title,
            "content": $content,
            "metadata": {
                "source": "sample_data",
                "type": "documentation"
            }
        }')
    
    # Upload document
    response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "$json_payload" \
        "$API_GATEWAY_URL/documents/upload")
    
    # Check response
    if echo "$response" | jq -e '.document_id' >/dev/null 2>&1; then
        echo -e "    ${GREEN}✅ Uploaded successfully${NC}"
    else
        echo -e "    ${RED}❌ Failed to upload${NC}"
        echo "    Response: $response"
    fi
}

# Check if jq is installed
if ! command -v jq >/dev/null 2>&1; then
    echo -e "${RED}jq is required but not installed. Please install jq first.${NC}"
    exit 1
fi

# Upload sample documents
echo "📤 Uploading sample documents..."

if [ -f "$DATA_DIR/aws_introduction.md" ]; then
    upload_document "$DATA_DIR/aws_introduction.md" "Introducción a AWS"
else
    echo -e "${YELLOW}⚠️  aws_introduction.md not found${NC}"
fi

if [ -f "$DATA_DIR/bedrock_overview.md" ]; then
    upload_document "$DATA_DIR/bedrock_overview.md" "Amazon Bedrock Overview"
else
    echo -e "${YELLOW}⚠️  bedrock_overview.md not found${NC}"
fi

if [ -f "$DATA_DIR/opensearch_guide.md" ]; then
    upload_document "$DATA_DIR/opensearch_guide.md" "Amazon OpenSearch Guide"
else
    echo -e "${YELLOW}⚠️  opensearch_guide.md not found${NC}"
fi

echo ""
echo "🎉 Sample documents upload completed!"
echo ""
echo "🧪 To test the chatbot, try asking:"
echo "  - '¿Qué es AWS?'"
echo "  - '¿Cómo funciona Amazon Bedrock?'"
echo "  - '¿Para qué sirve OpenSearch?'"
echo ""
echo "💡 You can also test using curl:"
echo "  curl -X POST $API_GATEWAY_URL/chat \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"message\": \"¿Qué es AWS?\"}'"

echo -e "${GREEN}✅ Upload script completed!${NC}"

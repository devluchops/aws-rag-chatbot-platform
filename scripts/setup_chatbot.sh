#!/bin/bash

# Script para configurar y probar el chatbot completo
echo "🚀 Configurando AWS Chatbot para pruebas completas..."
echo "====================================================="

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

ENV=${1:-dev}

echo -e "${YELLOW}Paso 1: Verificando infraestructura...${NC}"
API_URL=$(aws cloudformation describe-stacks --stack-name aws-chatbot --query 'Stacks[0].Outputs[?OutputKey==`ChatbotApiUrl`].OutputValue' --output text)
DOCS_BUCKET=$(aws ssm get-parameter --name "/chatbot/${ENV}/s3/documents_bucket" --query "Parameter.Value" --output text)
OPENSEARCH_ENDPOINT=$(aws ssm get-parameter --name "/chatbot/${ENV}/opensearch/endpoint" --query "Parameter.Value" --output text)

echo "✅ API URL: $API_URL"
echo "✅ Bucket de documentos: $DOCS_BUCKET"
echo "✅ OpenSearch endpoint: $OPENSEARCH_ENDPOINT"

echo -e "${YELLOW}Paso 2: Subiendo documentos a S3...${NC}"
aws s3 cp data/ s3://$DOCS_BUCKET/ --recursive
aws s3 ls s3://$DOCS_BUCKET/

echo -e "${YELLOW}Paso 3: Verificando API de salud...${NC}"
curl -s "${API_URL}health" | python3 -m json.tool

echo -e "${YELLOW}Paso 4: Probando endpoint de configuración...${NC}"
curl -s "${API_URL}config" | python3 -m json.tool

echo ""
echo -e "${GREEN}🎉 Configuración completada!${NC}"
echo "======================================="
echo "Para probar el chatbot:"
echo "1. Inicia el frontend: cd frontend && streamlit run app.py"
echo "2. Ve a http://localhost:8501"
echo "3. O usa el API directamente: $API_URL"
echo ""
echo "Endpoints disponibles:"
echo "- GET  ${API_URL}health"
echo "- GET  ${API_URL}config"
echo "- POST ${API_URL}chat"
echo "- POST ${API_URL}upload"

# AWS RAG Chatbot Platform

A production-ready, enterprise-grade RAG (Retrieval-Augmented Generation) chatbot platform built on AWS, featuring hybrid infrastructure management with Terraform and SAM, secure configuration management, and scalable architecture.

## 🚀 Quick Start

### Prerequisites
- **AWS CLI** configured with appropriate permissions
- **Terraform** v1.0+ installed
- **AWS SAM CLI** v1.80+ installed  
- **Python** 3.11+ with pip
- **Docker** (for SAM local development)
- **jq** (for JSON processing)

### One-Command Deployment
```bash
# Deploy complete development environment
make dev
```

### Deploy to Specific Environments
```bash
make staging    # Deploy to staging
make prod       # Deploy to production
make destroy ENV=dev  # Clean up development environment
```

## 🏗️ Architecture Overview

This platform implements a **hybrid cloud architecture** that separates infrastructure concerns from application logic:

```
┌─────────────────────────────────────────────────────────────────┐
│                    🌐 User Interface Layer                      │
├─────────────────────────────────────────────────────────────────┤
│  👤 User  ←→  🖥️ Streamlit Frontend  ←→  🌐 API Gateway         │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────────┐
│                    ⚡ Serverless Compute Layer                  │
├─────────────────────────────────────────────────────────────────┤
│                    🏢 VPC (Private Network)                     │
│  ┌─────────────────────┐    ┌───────────────────────────────┐   │
│  │  ⚡ Chat Lambda     │    │  ⚡ Document Processor      │   │
│  │  simple_handler.py  │    │  document_processor_lambda   │   │
│  └─────────────────────┘    └───────────────────────────────┘   │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────────┐
│                      💾 Data & AI Services                     │
├─────────────────────────────────────────────────────────────────┤
│  🔍 OpenSearch     📦 S3 Storage     🧠 Amazon Bedrock        │
│  Vector Database   Documents &       Titan Embeddings &        │
│  Document Index    Lambda Code       Claude 3 Chat            │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────────┐
│              ⚙️ Configuration & Security Layer                 │
├─────────────────────────────────────────────────────────────────┤
│  📋 SSM Parameters  🔐 Secrets Manager  📊 CloudWatch Logs     │
│  Configuration      OpenSearch Creds    Monitoring & Metrics   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                🏗️ Infrastructure Management                    │
├─────────────────────────────────────────────────────────────────┤
│  🏗️ Terraform           📦 AWS SAM           🌍 Multi-Env      │
│  VPC, OpenSearch        Lambda, API Gateway   dev/staging/prod  │
│  S3, SSM, Secrets       CloudWatch           Environment Isolation│
└─────────────────────────────────────────────────────────────────┘
```

### Infrastructure Layer (Terraform)
- **VPC & Networking**: Private subnets, security groups, NAT gateways
- **OpenSearch Domain**: Managed Elasticsearch for vector storage
- **S3 Buckets**: Document storage and Lambda code artifacts
- **Parameter Store**: Centralized configuration management
- **Secrets Manager**: Secure credential storage

### Application Layer (SAM)
- **Lambda Functions**: Serverless compute for chat and document processing
- **API Gateway**: RESTful API with CORS support
- **CloudWatch**: Logging and monitoring
- **IAM Roles**: Least-privilege access controls

### Data Flow
```
User Request → API Gateway → Lambda → OpenSearch → Bedrock → Response
                    ↓
             Document Processing → S3 → Lambda → OpenSearch (Indexing)
```

### Key Benefits
- 🔒 **Security First**: Zero hardcoded credentials, encryption at rest/transit
- 📈 **Auto-Scaling**: Serverless components scale automatically
- 🎯 **Environment Isolation**: Complete separation between dev/staging/prod
- 💰 **Cost-Optimized**: Pay-per-use serverless architecture
- 🔄 **CI/CD Ready**: Infrastructure as Code with GitOps support
- 📊 **Observable**: Comprehensive logging and monitoring

### Technology Stack
```
🖥️  Frontend:     Streamlit (Python)
🌐  API Layer:    AWS API Gateway + Lambda (Python 3.12)
🔍  Search:       Amazon OpenSearch (Vector Database)
🧠  AI/ML:        Amazon Bedrock (Titan + Claude)
📦  Storage:      Amazon S3 (Documents & Code)
⚙️  Config:       SSM Parameter Store + Secrets Manager
🏗️  Infrastructure: Terraform + AWS SAM
🌍  Environments: dev/staging/prod isolation
📊  Monitoring:   CloudWatch + CloudTrail
🔐  Security:     VPC, IAM, Encryption, Security Groups
```

## 📋 Available Commands

### Core Operations
```bash
make help                    # Show all available commands with descriptions
make deploy ENV=<env>        # Deploy complete stack to environment
make destroy ENV=<env>       # Safely destroy all resources
make status ENV=<env>        # Check deployment status and health
make config ENV=<env>        # Display current configuration
```

### Infrastructure Management
```bash
make deploy-infra ENV=<env>  # Deploy only infrastructure (Terraform)
make deploy-app ENV=<env>    # Deploy only application (SAM)
make validate                # Validate SAM template
```

### Development & Testing
```bash
make build                   # Build SAM application locally
make sam-local               # Start SAM local API (port 3000)
make run-local               # Run backend with uvicorn (port 8000)
make run-frontend            # Start Streamlit frontend (port 8501)
make test                    # Run pytest test suite
make test-api ENV=<env>      # Execute API endpoint tests
make test-chatbot ENV=<env>  # Test complete chatbot functionality
```

### Data & Setup
```bash
make upload-data             # Upload sample documents for testing
make setup-chatbot ENV=<env> # Complete chatbot setup and verification
make setup                   # Setup local development environment
make install                 # Install Python dependencies
```

### Docker Operations
```bash
make run-docker              # Start application with Docker Compose
make stop-docker             # Stop Docker Compose containers
make logs                    # Show application logs
```

### Monitoring & Debugging
```bash
make sam-logs ENV=<env>      # Tail Lambda function logs in real-time
make env-info                # Show current environment information
make clean                   # Clean temporary files and build artifacts
```

### Environment Shortcuts
```bash
make dev                     # Quick deploy to development
make staging                 # Quick deploy to staging  
make prod                    # Quick deploy to production
```

## 🔧 Configuration Management

### SSM Parameter Store Hierarchy
```
/${PROJECT_NAME}/${ENVIRONMENT}/
├── vpc/
│   ├── id                   # VPC ID (vpc-xxxxxxxxx)
│   ├── subnet_ids           # Private subnet IDs (comma-separated)
│   └── security_group_id    # Lambda security group ID
├── opensearch/
│   ├── endpoint             # OpenSearch domain endpoint
│   ├── username             # Master username (admin)
│   └── domain_name          # Domain name for reference
├── s3/
│   ├── documents_bucket     # Document storage bucket name
│   └── lambda_code_bucket   # Lambda deployment artifacts bucket
├── bedrock/
│   ├── embedding_model      # Model ID for embeddings
│   └── chat_model          # Model ID for chat responses
└── app/
    ├── aws_region           # Deployment region
    ├── project_name         # Project identifier
    └── environment          # Environment name (dev/staging/prod)
```

### Secrets Manager Schema
```json
{
  "SecretId": "${PROJECT_NAME}-${ENVIRONMENT}-opensearch-credentials",
  "SecretString": {
    "username": "admin",
    "password": "auto-generated-secure-password",
    "endpoint": "vpc-domain-xyz.region.es.amazonaws.com"
  }
}
```

### Environment Variables (Lambda)
```bash
ENVIRONMENT=dev                                    # Target environment
PROJECT_NAME=aws-chatbot                          # Project identifier  
SSM_PARAMETER_PREFIX=/aws-chatbot/dev             # SSM parameter path
OPENSEARCH_SECRET_NAME=aws-chatbot-dev-opensearch-credentials
AWS_REGION=us-east-1                              # Automatically provided
```

## 📁 Project Structure

```
aws-rag-chatbot-platform/
├── 📄 Makefile                      # Automation commands and workflows
├── 📄 template.yaml                 # SAM template (serverless components)
├── 📄 README.md                     # This comprehensive guide
├── 📄 samconfig.toml                # SAM CLI configuration
├── 📄 .gitignore                    # Git ignore patterns
│
├── � backend/                      # Python application source code
│   ├── 📄 Dockerfile                # Container configuration for Lambda
│   ├── 📄 requirements.txt          # Python dependencies
│   ├── � run.sh                    # Local development runner
│   └── 📂 src/                      # Source code following Python best practices
│       ├── � __init__.py           # Package initialization
│       ├── 📄 README.md             # Backend-specific documentation
│       ├── � .env.example          # Environment variables template
│       ├── 📂 handlers/             # Lambda function handlers
│       ├── 📂 services/             # Business logic layer
│       ├── 📂 models/               # Data models and schemas
│       ├── 📂 core/                 # Core utilities and configuration
│       └── 📂 api/                  # API-specific modules
│
├── 📂 frontend/                     # Frontend application (Streamlit)
│   ├── 📄 requirements.txt          # Frontend Python dependencies
│   └── 📄 app.py                    # Streamlit application
│
├── 📂 terraform/                    # Infrastructure as Code
│   ├── 📄 0-provider.tf             # AWS provider configuration
│   ├── 📄 1-terraform.tf            # Terraform backend configuration
│   ├── 📄 2-resources-vpc.tf        # VPC, subnets, security groups
│   ├── 📄 2-resources-opensearch.tf # OpenSearch domain configuration
│   ├── 📄 2-resources-s3.tf         # S3 buckets and policies
│   ├── 📄 2-resources-ssm.tf        # SSM parameters and Secrets Manager
│   ├── 📄 2-resources-bedrock.tf    # Bedrock model access configuration
│   ├── 📄 3-variables.tf            # Input variables definition
│   ├── 📄 4-outputs.tf              # Output values for SAM integration
│   ├── 📄 terraform.tfstate         # Terraform state file
│   └── 📂 environments/             # Environment-specific configurations
│       ├── 📄 dev.tfvars            # Development environment variables
│       ├── 📄 staging.tfvars        # Staging environment variables
│       └── 📄 prod.tfvars           # Production environment variables
│
├── 📂 scripts/                      # Essential utility scripts
│   ├── 📄 setup_local.sh            # Local development environment setup
│   ├── 📄 setup_chatbot.sh          # Complete chatbot configuration and testing
│   └── 📄 upload_sample_data.sh     # Upload sample documents for testing
│
├── 📂 tests/                        # Test suites
│   └── 📄 conftest.py               # Pytest configuration
│
└── 📂 data/                         # Sample data and documentation
    ├── 📄 aws_bedrock_guide.md      # AWS Bedrock usage guide
    ├── 📄 aws_introduction.md       # AWS services introduction
    ├── 📄 bedrock_overview.md       # Bedrock capabilities overview
    └── 📄 opensearch_guide.md       # OpenSearch implementation guide
```

### Key Directories Explained

- **`backend/`**: Contains all Python application code with proper package structure
- **`frontend/`**: Streamlit web interface for interactive chat
- **`terraform/`**: Infrastructure definitions following Terraform best practices
- **`scripts/`**: Essential setup and data management utilities
- **`tests/`**: Automated testing suite for quality assurance
- **`data/`**: Sample documents and knowledge base content
│   └── username             # OpenSearch username
├── s3/
│   └── documents_bucket     # S3 bucket name
└── app/
    ├── aws_region           # AWS region
    └── project_name         # Project name
```

### Secrets Manager
```
${PROJECT_NAME}-${ENVIRONMENT}-opensearch-credentials
└── {
    "username": "admin",
    "password": "generated-password"
}
```

## 🛠️ Deployment Process

### Phase 1: Infrastructure Deployment (Terraform)
```bash
# Deploy infrastructure components
make deploy-infra ENV=dev
```

**What gets deployed:**
- ✅ VPC with public/private subnets across multiple AZs
- ✅ NAT Gateway for secure outbound internet access
- ✅ Security Groups with least-privilege access rules
- ✅ OpenSearch domain with encryption at rest/transit
- ✅ S3 buckets with versioning and encryption
- ✅ IAM roles and policies for Lambda execution
- ✅ SSM Parameter Store entries for configuration
- ✅ Secrets Manager for sensitive credentials

### Phase 2: Application Deployment (SAM)
```bash
# Deploy serverless application components
make deploy-app ENV=dev
```

**What gets deployed:**
- ✅ Lambda functions with VPC configuration
- ✅ API Gateway with CORS and authentication
- ✅ CloudWatch Log Groups with retention policies
- ✅ Lambda layers for shared dependencies
- ✅ S3 event triggers for document processing
- ✅ Dead letter queues for error handling

### Phase 3: Complete Deployment (Automated)
```bash
# Deploy everything in correct order
make deploy ENV=dev
```

**Full deployment includes:**
1. **Pre-deployment validation** of AWS credentials and permissions
2. **Infrastructure provisioning** with Terraform state management
3. **Application packaging** and dependency resolution
4. **Serverless deployment** with automatic configuration injection
5. **Post-deployment testing** and health checks
6. **Configuration verification** and endpoint testing

### Deployment Validation
```bash
# Check deployment status
make status ENV=dev

# Validate API endpoints
make test-api ENV=dev

# Upload sample data for testing
make upload-data ENV=dev
```

## 🔍 API Documentation

### Health Check Endpoint
```bash
# Check service health
curl -X GET https://{api-id}.execute-api.{region}.amazonaws.com/Prod/health

# Expected Response
{
  "status": "healthy",
  "message": "AWS Chatbot API is running",
  "timestamp": "2025-01-18T10:30:00Z",
  "environment": "dev",
  "version": "1.0.0"
}
```

### Chat Endpoint
```bash
# Send chat message
curl -X POST https://{api-id}.execute-api.{region}.amazonaws.com/Prod/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is AWS Bedrock?",
    "chat_history": [],
    "max_results": 5
  }'

# Expected Response
{
  "message": "AWS Bedrock is a fully managed service...",
  "confidence": 0.95,
  "sources": [
    {
      "document": "aws_bedrock_guide.md",
      "relevance_score": 0.98
    }
  ],
  "timestamp": "2025-01-18T10:30:15Z"
}
```

### Document Processing Endpoint
```bash
# Upload and process document
curl -X POST https://{api-id}.execute-api.{region}.amazonaws.com/Prod/process-document \
  -H "Content-Type: application/json" \
  -d '{
    "s3_bucket": "your-documents-bucket",
    "s3_key": "documents/new-document.pdf"
  }'
```

## 🔍 Monitoring & Debugging

### Check Deployment Status
```bash
make status ENV=dev
```

### View Configuration
```bash
make config ENV=dev
```

### View Logs
```bash
make sam-logs ENV=dev
```

### Test API
```bash
make test-api ENV=dev
```

## 🌍 Environment Management

### Development Environment
```bash
# Quick development deployment
make dev

# Development-specific commands
make config ENV=dev          # Show development configuration
make sam-logs ENV=dev        # Monitor development logs
make test-api ENV=dev        # Test development endpoints
make destroy ENV=dev         # Clean up development resources
```

**Development Environment Features:**
- Lower-cost instance types for cost optimization
- Detailed logging for debugging
- Sample data pre-loaded
- Relaxed security for faster iteration

### Staging Environment
```bash
# Deploy to staging for pre-production testing
make staging

# Staging-specific validation
make config ENV=staging      # Show staging configuration
make test-api ENV=staging    # Run staging test suite
make destroy ENV=staging     # Clean up staging resources
```

**Staging Environment Features:**
- Production-like configuration
- Performance testing enabled
- Integration testing with external services
- Blue-green deployment testing

### Production Environment
```bash
# Deploy to production with extra validations
make prod

# Production monitoring
make config ENV=prod         # Show production configuration
make sam-logs ENV=prod       # Monitor production logs (filtered)
make destroy ENV=prod        # Clean up production (requires confirmation)
```

**Production Environment Features:**
- High-availability multi-AZ deployment
- Enhanced monitoring and alerting
- Backup and disaster recovery
- Strict security and compliance controls

## 🔧 Local Development

### Prerequisites for Local Development
```bash
# Install backend Python dependencies
pip install -r backend/requirements.txt

# Install frontend Python dependencies (if using Streamlit)
pip install -r frontend/requirements.txt

# Configure AWS credentials
aws configure

# Set environment variables
export ENVIRONMENT=local
export PROJECT_NAME=aws-chatbot
```

### Backend Development
```bash
# Start backend with hot-reload
make run-local

# The server starts on http://localhost:8000
# API endpoints:
# - GET  /health
# - POST /chat
# - POST /process-document
```

### SAM Local Development
```bash
# Start SAM local API Gateway
make sam-local

# Test local endpoints
curl http://localhost:3000/health
curl -X POST http://localhost:3000/chat -d '{"message": "test"}'
```

### Frontend Development (Streamlit)
```bash
# Start Streamlit frontend
make run-frontend

# Manual start (alternative)
cd frontend && streamlit run app.py --server.port=8501

# The frontend opens at http://localhost:8501
```

### Docker Development (Complete Stack)
```bash
# Start complete application stack
make run-docker

# View logs
make logs

# Stop containers
make stop-docker
```

### Testing and Quality Assurance
```bash
# Run unit tests with pytest
make test

# Test API endpoints
make test-api ENV=dev

# Test complete chatbot functionality
make test-chatbot ENV=dev

# Clean up temporary files
make clean
```

## 📊 Monitoring & Observability

### CloudWatch Integration
- **Lambda Functions**: Automatic logging with configurable retention
- **API Gateway**: Request/response logging and metrics
- **OpenSearch**: Cluster health and performance metrics
- **Custom Metrics**: Application-specific KPIs and business metrics

### Available Monitoring Commands
```bash
# Real-time log monitoring
make sam-logs ENV=dev

# Check deployment health
make status ENV=dev

# View application metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=aws-chatbot-ChatbotFunction

# Monitor API Gateway metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name Count \
  --dimensions Name=ApiName,Value=aws-chatbot-dev-api
```

### Log Analysis
```bash
# Search logs for specific patterns
aws logs filter-log-events \
  --log-group-name /aws/lambda/aws-chatbot-ChatbotFunction \
  --filter-pattern "ERROR"

# Download logs for offline analysis
aws logs create-export-task \
  --log-group-name /aws/lambda/aws-chatbot-ChatbotFunction \
  --from 1609459200000 \
  --to 1609545600000 \
  --destination your-log-bucket
```

## 🆘 Troubleshooting Guide

### Common Issues and Solutions

#### 1. **Deployment Failures**
```bash
# Check deployment status
make status ENV=dev

# Validate templates before deployment
make validate

# View detailed error logs
make sam-logs ENV=dev

# Common fixes:
# - Verify AWS credentials: aws sts get-caller-identity
# - Check region consistency across all configs
# - Ensure sufficient IAM permissions
```

#### 2. **Configuration Issues**
```bash
# Verify all configuration parameters
make config ENV=dev

# Check specific SSM parameters
aws ssm get-parameter --name "/aws-chatbot/dev/opensearch/endpoint"

# Validate secrets
aws secretsmanager get-secret-value --secret-id aws-chatbot-dev-opensearch-credentials

# Common fixes:
# - Re-run infrastructure deployment: make deploy-infra ENV=dev
# - Check parameter paths match between Terraform and SAM
```

#### 3. **API Gateway Errors**
```bash
# Test API health
make test-api ENV=dev

# Check API Gateway logs
aws logs filter-log-events \
  --log-group-name API-Gateway-Execution-Logs_{api-id}/{stage} \
  --filter-pattern "ERROR"

# Common fixes:
# - Verify CORS configuration
# - Check Lambda function permissions
# - Validate request/response format
```

#### 4. **Lambda Function Issues**
```bash
# Monitor function logs in real-time
make sam-logs ENV=dev

# Check function configuration
aws lambda get-function-configuration \
  --function-name aws-chatbot-ChatbotFunction

# Common fixes:
# - Increase memory/timeout settings
# - Verify VPC configuration
# - Check environment variables
```

#### 5. **OpenSearch Connection Problems**
```bash
# Test OpenSearch connectivity from Lambda VPC
aws ec2 describe-vpc-endpoints \
  --filters Name=service-name,Values=com.amazonaws.{region}.es

# Verify security group rules
aws ec2 describe-security-groups \
  --group-ids {security-group-id}

# Common fixes:
# - Check security group allows HTTPS (443) traffic
# - Verify Lambda is in correct subnets
# - Confirm OpenSearch domain policy
```

### Emergency Procedures

#### Complete Environment Reset
```bash
# Step 1: Destroy everything safely
make destroy ENV=dev

# Step 2: Clean up any remaining resources manually if needed
aws cloudformation delete-stack --stack-name aws-chatbot
aws s3 rm s3://aws-chatbot-dev-documents-* --recursive

# Step 3: Redeploy from scratch
make deploy ENV=dev
```

### Performance Optimization

#### Lambda Cold Start Optimization
```yaml
# In template.yaml
ProvisionedConcurrencyConfig:
  ProvisionedConcurrencyUnits: 5

# Environment variable optimization
Variables:
  PYTHONPATH: /var/task
  AWS_LAMBDA_EXEC_WRAPPER: /opt/bootstrap
```

#### OpenSearch Performance Tuning
```bash
# Monitor cluster health
aws es describe-elasticsearch-domain \
  --domain-name chatbot-dev

# Optimize index settings
curl -X PUT "https://{opensearch-endpoint}/chatbot-documents/_settings" \
  -H "Content-Type: application/json" \
  -d '{
    "index": {
      "number_of_replicas": 0,
      "refresh_interval": "30s"
    }
  }'
```

## 🔗 Quick Reference & Cheat Sheet

### Essential Commands
```bash
# Development workflow
make dev                     # Deploy development environment
make status ENV=dev          # Check deployment health
make test-chatbot ENV=dev    # Test complete functionality
make destroy ENV=dev         # Clean up resources

# Local development
make setup                   # Setup local environment
make run-local              # Start backend server
make run-frontend           # Start Streamlit interface

# Emergency commands
make help                   # Show all available commands
make clean                  # Clean temporary files
```

### Useful AWS CLI Commands
```bash
# Check deployment status
aws cloudformation describe-stacks --stack-name aws-chatbot

# List Lambda functions
aws lambda list-functions --query "Functions[?contains(FunctionName, 'chatbot')]"

# Get API Gateway URL
aws apigateway get-rest-apis --query "items[?name=='aws-chatbot-dev-api']"

# Monitor OpenSearch
aws es describe-elasticsearch-domain --domain-name chatbot-dev
```

### Configuration Quick Check
```bash
# Verify all required parameters exist
aws ssm get-parameters-by-path --path "/aws-chatbot/dev" --recursive

# Test OpenSearch connectivity
curl -X GET "https://{opensearch-endpoint}/_cluster/health"

# Validate Bedrock model access
aws bedrock list-foundation-models --region us-east-1
```

## 📚 Additional Resources

### Documentation
- **[Complete Architecture Diagrams](ARCHITECTURE.md)** - Detailed system architecture with Mermaid diagrams
- **[Backend README](backend/src/README.md)** - Backend-specific documentation and setup
- **[Sample Data](data/)** - Knowledge base documents and guides

### External Resources
- **[AWS SAM Documentation](https://docs.aws.amazon.com/serverless-application-model/)**
- **[Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)**
- **[OpenSearch Documentation](https://opensearch.org/docs/latest/)**
- **[AWS Bedrock Developer Guide](https://docs.aws.amazon.com/bedrock/latest/userguide/)**

### Community and Support
- **GitHub Issues**: Report bugs and request features
- **Discussions**: Share use cases and get community help
- **Wiki**: Additional examples and community contributions

## 🎯 Getting Started Checklist

### Initial Setup (One-time)
- [ ] Install all prerequisites (AWS CLI, Terraform, SAM CLI, Python 3.11+)
- [ ] Configure AWS credentials with appropriate permissions
- [ ] Clone repository and review project structure
- [ ] Read architecture documentation

### First Deployment
- [ ] Deploy development environment: `make dev`
- [ ] Verify deployment status: `make status ENV=dev`
- [ ] Setup chatbot configuration: `make setup-chatbot ENV=dev`
- [ ] Upload sample data: `make upload-data`
- [ ] Test API endpoints: `make test-api ENV=dev`
- [ ] Test complete functionality: `make test-chatbot ENV=dev`

### Next Steps
- [ ] Customize environment variables in `terraform/environments/`
- [ ] Add your own documents using `make upload-data`
- [ ] Explore the Streamlit frontend with `make run-frontend`
- [ ] Set up monitoring and alerting for production
- [ ] Implement additional security measures as needed

---

## 🏆 Success Metrics

After successful deployment, you should have:

✅ **Scalable Infrastructure**: Auto-scaling serverless architecture  
✅ **Secure Configuration**: No hardcoded credentials, encrypted storage  
✅ **Multi-Environment**: Isolated dev/staging/prod environments  
✅ **Monitoring**: Comprehensive logging and metrics  
✅ **Frontend**: Interactive Streamlit chat interface  
✅ **Automation**: One-command deployment and management  

**Ready to deploy?** Start with `make dev` and begin building your AI-powered knowledge platform!

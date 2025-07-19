# Makefile for AWS RAG Chatbot

.PHONY: help setup install deploy upload-data test clean destroy validate build status

# Colors
RED=\033[0;31m
GREEN=\033[0;32m
YELLOW=\033[1;33m
NC=\033[0m # No Color

# Default environment
ENV ?= dev
PROJECT_NAME ?= aws-chatbot

help: ## Show this help message
	@echo "AWS RAG Chatbot - Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Setup local development environment
	@echo "$(GREEN)Setting up local development environment...$(NC)"
	@./scripts/setup_local.sh

install: ## Install Python dependencies
	@echo "$(GREEN)Installing Python dependencies...$(NC)"
	@pip install --upgrade pip setuptools wheel
	@pip install -r requirements.txt

validate: ## Validate SAM template
	@echo "$(GREEN)Validating SAM template...$(NC)"
	@sam validate

build: ## Build SAM application
	@echo "$(GREEN)Building SAM application...$(NC)"
	@sam build --use-container

deploy: ## Deploy infrastructure and application (ENV=dev/staging/prod)
	@echo "$(GREEN)Deploying to $(ENV) environment...$(NC)"
	@echo "$(YELLOW)Loading environment variables...$(NC)"
	@source .env && echo "Environment variables loaded"
	@echo "$(YELLOW)Step 1: Deploying infrastructure with Terraform...$(NC)"
	@source .env && cd terraform && terraform init
	@source .env && cd terraform && terraform apply -var-file="environments/$(ENV).tfvars" -auto-approve
	@echo "$(YELLOW)Step 2: Building and deploying serverless components...$(NC)"
	@sam build --use-container
	$(eval S3_BUCKET := $(shell source .env && aws ssm get-parameter --name "/chatbot/$(ENV)/s3/lambda_code_bucket" --query "Parameter.Value" --output text))
	@source .env && sam deploy --s3-bucket $(S3_BUCKET) --parameter-overrides Environment=$(ENV) ProjectName=$(PROJECT_NAME) --no-confirm-changeset
	@echo "$(GREEN)✅ Deployment completed successfully!$(NC)"
	@echo "$(GREEN)📋 Getting deployment information...$(NC)"
	@make status

deploy-infra: ## Deploy only infrastructure (Terraform)
	@echo "$(GREEN)Deploying infrastructure to $(ENV) environment...$(NC)"
	@cd terraform && terraform init
	@cd terraform && terraform apply -var-file="environments/$(ENV).tfvars" -auto-approve
	@echo "$(GREEN)✅ Infrastructure deployment completed!$(NC)"

deploy-app: ## Deploy only application (SAM)
	@echo "$(GREEN)Deploying application to $(ENV) environment...$(NC)"
	@sam build
	$(eval S3_BUCKET := $(shell aws ssm get-parameter --name "/chatbot/$(ENV)/s3/lambda_code_bucket" --query "Parameter.Value" --output text))
	@sam deploy --s3-bucket $(S3_BUCKET) --parameter-overrides Environment=$(ENV) ProjectName=$(PROJECT_NAME) --no-confirm-changeset
	@echo "$(GREEN)✅ Application deployment completed!$(NC)"

upload-data: ## Upload sample data to the chatbot
	@echo "$(GREEN)Uploading sample data...$(NC)"
	@./scripts/upload_sample_data.sh

test: ## Run tests
	@echo "$(GREEN)Running tests...$(NC)"
	@python -m pytest tests/ -v

test-api: ## Test API endpoints
	@echo "$(GREEN)Testing API endpoints...$(NC)"
	@aws cloudformation describe-stacks --stack-name $(PROJECT_NAME)-$(ENV) --query 'Stacks[0].Outputs[?OutputKey==`ChatbotApiUrl`].OutputValue' --output text 2>/dev/null | xargs -I {} curl -X POST {}/health || echo "API Gateway URL not found"

run-local: ## Run backend server locally
	@echo "$(GREEN)Starting backend server locally...$(NC)"
	@cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000

run-frontend: ## Run frontend application locally
	@echo "$(GREEN)Starting frontend application locally...$(NC)"
	@echo "$(YELLOW)Make sure you have streamlit installed: pip install streamlit$(NC)"
	@cd frontend && streamlit run app.py --server.port=8501

setup-chatbot: ## Setup chatbot for testing (upload docs, verify config)
	@echo "$(GREEN)Setting up chatbot for testing...$(NC)"
	@./scripts/setup_chatbot.sh $(ENV)

test-chatbot: ## Test chatbot functionality
	@echo "$(GREEN)Testing chatbot functionality...$(NC)"
	$(eval API_URL := $(shell aws cloudformation describe-stacks --stack-name aws-chatbot --query 'Stacks[0].Outputs[?OutputKey==`ChatbotApiUrl`].OutputValue' --output text))
	@echo "$(YELLOW)API URL: $(API_URL)$(NC)"
	@echo "$(YELLOW)Testing health endpoint...$(NC)"
	@curl -s "$(API_URL)health" | python3 -m json.tool
	@echo "$(YELLOW)Testing config endpoint...$(NC)"
	@curl -s "$(API_URL)config" | python3 -m json.tool

run-docker: ## Run application with Docker Compose
	@echo "$(GREEN)Starting application with Docker Compose...$(NC)"
	@docker-compose up -d

stop-docker: ## Stop Docker Compose
	@echo "$(GREEN)Stopping Docker Compose...$(NC)"
	@docker-compose down

logs: ## Show application logs
	@echo "$(GREEN)Showing application logs...$(NC)"
	@docker-compose logs -f

clean: ## Clean up temporary files
	@echo "$(GREEN)Cleaning up temporary files...$(NC)"
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@rm -rf .pytest_cache
	@rm -rf .aws-sam
	@rm -rf backend/__pycache__
	@echo "$(GREEN)Cleanup completed$(NC)"

destroy: ## Destroy AWS infrastructure
	@echo "$(YELLOW)Destroying AWS infrastructure for $(ENV) environment...$(NC)"
	@echo "$(YELLOW)Loading environment variables...$(NC)"
	@source .env && echo "Environment variables loaded"
	@echo "$(YELLOW)Step 1: Destroying SAM stack...$(NC)"
	@source .env && if aws cloudformation describe-stacks --stack-name $(PROJECT_NAME)-$(ENV) >/dev/null 2>&1; then \
		echo "$(YELLOW)Stack exists, proceeding with deletion...$(NC)"; \
		aws cloudformation delete-stack --stack-name $(PROJECT_NAME)-$(ENV); \
		echo "$(YELLOW)Waiting for SAM stack deletion to complete...$(NC)"; \
		aws cloudformation wait stack-delete-complete --stack-name $(PROJECT_NAME)-$(ENV); \
		echo "$(GREEN)✅ SAM stack destroyed successfully!$(NC)"; \
	else \
		echo "$(YELLOW)Stack $(PROJECT_NAME)-$(ENV) does not exist, skipping...$(NC)"; \
	fi
	@echo "$(YELLOW)Step 2: Destroying Terraform infrastructure...$(NC)"
	@source .env && cd terraform && terraform destroy -var-file="environments/$(ENV).tfvars" -auto-approve
	@echo "$(GREEN)✅ Infrastructure destroyed successfully!$(NC)"

status: ## Show deployment status
	@echo "$(GREEN)Checking deployment status for $(ENV) environment...$(NC)"
	@echo "$(YELLOW)Terraform Resources:$(NC)"
	@cd terraform && terraform output -json | jq -r 'to_entries[] | "\(.key): \(.value.value)"' 2>/dev/null || echo "No Terraform outputs found"
	@echo "$(YELLOW)SAM Stack:$(NC)"
	@aws cloudformation describe-stacks --stack-name $(PROJECT_NAME) --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' --output table 2>/dev/null || echo "SAM stack not found"
	@echo "$(YELLOW)SSM Parameters:$(NC)"
	@aws ssm get-parameters-by-path --path "/chatbot/$(ENV)" --recursive --query 'Parameters[*].[Name,Value]' --output table 2>/dev/null || echo "No SSM parameters found"

config: ## Show configuration for environment
	@echo "$(GREEN)Configuration for $(ENV) environment:$(NC)"
	@echo "$(YELLOW)SSM Parameters:$(NC)"
	@aws ssm get-parameters-by-path --path "/chatbot/$(ENV)" --recursive --query 'Parameters[*].[Name,Value]' --output table 2>/dev/null || echo "No SSM parameters found"
	@echo "$(YELLOW)Secrets:$(NC)"
	@aws secretsmanager list-secrets --filters Key=name,Values=$(PROJECT_NAME)-$(ENV) --query 'SecretList[*].[Name,Description]' --output table 2>/dev/null || echo "No secrets found"

# Quick commands
dev: ## Deploy to development environment
	@make deploy ENV=dev

staging: ## Deploy to staging environment
	@make deploy ENV=staging

prod: ## Deploy to production environment
	@make deploy ENV=prod

# Development helpers
sam-local: ## Start SAM local API
	@echo "$(GREEN)Starting SAM local API...$(NC)"
	@sam local start-api

sam-logs: ## Tail SAM Lambda logs
	@echo "$(GREEN)Tailing Lambda logs...$(NC)"
	@sam logs -n $(PROJECT_NAME)-$(ENV)-ChatbotFunction --stack-name $(PROJECT_NAME)-$(ENV) --tail

# Environment info
env-info: ## Show environment information
	@echo "$(GREEN)Environment Information:$(NC)"
	@echo "Environment: $(ENV)"
	@echo "Project Name: $(PROJECT_NAME)"
	@echo "AWS Region: $$(aws configure get region)"
	@echo "AWS Profile: $$(aws configure get profile || echo 'default')"

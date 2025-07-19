# Backend Source Code

This directory contains the organized source code for the AWS Chatbot backend.

## Structure

- `handlers/` - Lambda function handlers
- `api/` - FastAPI application and routes
- `services/` - Business logic services
- `models/` - Data models and schemas
- `core/` - Core utilities and configuration

## Usage

All Lambda handlers are in `handlers/` and can be referenced in the SAM template as:
- `src.handlers.simple_handler.lambda_handler`
- `src.handlers.document_processor_lambda.lambda_handler`

import json
import boto3
import os
from typing import Dict, Any
from datetime import datetime

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Simple Lambda handler for health check and basic API functionality
    """
    print(f"Event: {json.dumps(event)}")
    
    # Get HTTP method and path
    http_method = event.get('httpMethod', 'GET')
    path = event.get('path', '/')
    
    # Basic routing
    if path == '/health' and http_method == 'GET':
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization'
            },
            'body': json.dumps({
                'status': 'healthy',
                'message': 'AWS Chatbot API is running',
                'timestamp': '2025-07-18T19:51:09.138Z',
                'environment': os.environ.get('ENVIRONMENT', 'dev'),
                'version': '1.0.0'
            })
        }
    
    # Test SSM parameter access
    elif path == '/config' and http_method == 'GET':
        try:
            ssm_client = boto3.client('ssm')
            env = os.environ.get('ENVIRONMENT', 'dev')
            
            # Try to get some SSM parameters
            response = ssm_client.get_parameters_by_path(
                Path=f'/chatbot/{env}',
                Recursive=True
            )
            
            parameters = {param['Name']: param['Value'] for param in response['Parameters']}
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'status': 'success',
                    'parameters': parameters,
                    'environment': env
                })
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'status': 'error',
                    'message': str(e)
                })
            }
    
    # Create OpenSearch index
    elif path == '/create-index' and http_method == 'POST':
        try:
            from src.services.opensearch_service import OpenSearchService
            os_service = OpenSearchService()
            
            # Force create index even in Lambda environment
            os_service._create_index_if_not_exists()
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'status': 'success',
                    'message': 'Index created successfully'
                })
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'status': 'error',
                    'message': str(e)
                })
            }
    
    # Process documents from S3
    elif path == '/process-s3-docs' and http_method == 'POST':
        try:
            import boto3
            from src.services.opensearch_service import OpenSearchService
            from src.core.utils.environment import get_environment_config
            
            # Get S3 bucket name
            config = get_environment_config()
            ssm_client = boto3.client('ssm', region_name=config['aws_region'])
            bucket_response = ssm_client.get_parameter(Name='/chatbot/dev/s3/documents_bucket')
            bucket_name = bucket_response['Parameter']['Value']
            
            # List and process documents from S3
            s3_client = boto3.client('s3')
            os_service = OpenSearchService()
            
            # List objects in bucket
            response = s3_client.list_objects_v2(Bucket=bucket_name)
            processed_count = 0
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    key = obj['Key']
                    
                    try:
                        # Download file content
                        file_response = s3_client.get_object(Bucket=bucket_name, Key=key)
                        content = file_response['Body'].read().decode('utf-8')
                        
                        # Extract title from filename
                        title = key.replace('.md', '').replace('_', ' ').title()
                        
                        # Index document
                        os_service._index_document_sync(
                            title=title,
                            content=content,
                            metadata={
                                'source': 's3',
                                'bucket': bucket_name,
                                'key': key,
                                'processed_at': datetime.now().isoformat()
                            }
                        )
                        processed_count += 1
                        print(f"Processed document: {title}")
                        
                    except Exception as doc_error:
                        print(f"Error processing {key}: {doc_error}")
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'status': 'success',
                    'message': f'Processed {processed_count} documents from S3',
                    'processed_count': processed_count,
                    'bucket': bucket_name
                })
            }
            
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'status': 'error',
                    'message': str(e)
                })
            }
    
    # Test OpenSearch connectivity
    elif path == '/opensearch-test' and http_method == 'GET':
        try:
            from src.services.opensearch_service import OpenSearchService
            os_service = OpenSearchService()
            
            # Test connection
            info = os_service.client.info()
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'status': 'success',
                    'opensearch_info': info,
                    'message': 'OpenSearch is accessible'
                })
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'status': 'error',
                    'message': f'OpenSearch connection failed: {str(e)}'
                })
            }

    # Chat endpoint
    elif path == '/chat' and http_method == 'POST':
        try:
            # Parse request
            payload = json.loads(event.get('body', '{}'))
            message = payload.get('message', '')
            chat_history = payload.get('chat_history', [])
            max_results = payload.get('max_results', 5)
            
            # Try RAG workflow first
            try:
                import asyncio
                from src.services.opensearch_service import OpenSearchService
                from src.services.rag_service import RAGService
                os_service = OpenSearchService()
                rag_service = RAGService()
                # Perform document search and generate answer
                docs = asyncio.run(os_service.search_documents(message, max_results))
                rag_resp = asyncio.run(rag_service.generate_response(message, docs, chat_history))
                response_body = {
                    'message': rag_resp['answer'],
                    'confidence': rag_resp['confidence'],
                    'sources': rag_resp['sources'],
                    'timestamp': rag_resp['timestamp']
                }
            except Exception as rag_error:
                # Fallback to mock response if RAG fails
                response_body = {
                    'message': f"⚠️ RAG system is not fully configured yet. Mock response for: '{message}'\n\nTo enable full RAG functionality, please:\n1. Enable Bedrock model access in AWS Console\n2. Request access to 'Amazon Titan Text Embeddings V1'\n3. Request access to 'Claude 3 Haiku' or 'Claude 3.5 Sonnet'\n\nError details: {str(rag_error)}",
                    'confidence': 0.0,
                    'sources': [],
                    'timestamp': datetime.now().isoformat()
                }
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization'
                },
                'body': json.dumps(response_body)
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'message': str(e)})
            }
    
    # Default response
    return {
        'statusCode': 404,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'status': 'error',
            'message': 'Not found',
            'path': path,
            'method': http_method
        })
    }

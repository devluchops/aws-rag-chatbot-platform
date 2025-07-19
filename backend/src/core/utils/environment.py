import os
import asyncio
from functools import wraps
from typing import Union, Callable, Any

def sync_async_compatible(func):
    """
    Decorator para hacer que una función funcione tanto en modo síncrono como asíncrono
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Si estamos en un contexto async, usar await
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Ya estamos en un contexto async, ejecutar directamente
                return func(*args, **kwargs)
            else:
                # No hay loop corriendo, crear uno
                return asyncio.run(func(*args, **kwargs))
        except RuntimeError:
            # No hay loop, ejecutar síncronamente
            return func(*args, **kwargs)
    
    return wrapper

def is_lambda_environment() -> bool:
    """Detectar si estamos corriendo en Lambda"""
    return os.getenv('AWS_LAMBDA_FUNCTION_NAME') is not None

def get_environment_config() -> dict:
    """Obtener configuración basada en el entorno"""
    if is_lambda_environment():
        import boto3
        
        # Obtener parámetros de SSM
        ssm_client = boto3.client('ssm', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
        
        try:
            # Obtener endpoint desde SSM
            endpoint_response = ssm_client.get_parameter(Name='/chatbot/dev/opensearch/endpoint')
            endpoint = endpoint_response['Parameter']['Value']
            
            # Obtener username desde SSM
            username_response = ssm_client.get_parameter(Name='/chatbot/dev/opensearch/username')
            username = username_response['Parameter']['Value']
            
            # Obtener password desde SSM
            password_response = ssm_client.get_parameter(Name='/chatbot/dev/opensearch/password', WithDecryption=True)
            password = password_response['Parameter']['Value']
            
            return {
                'opensearch_endpoint': endpoint,
                'opensearch_username': username, 
                'opensearch_password': password,
                'aws_region': os.environ.get('AWS_REGION', 'us-east-1'),
            }
        except Exception as e:
            raise Exception(f"Failed to get OpenSearch configuration from SSM: {str(e)}")
    else:
        # Desarrollo local con .env
        from dotenv import load_dotenv
        load_dotenv()
        
        return {
            'opensearch_endpoint': os.getenv('OPENSEARCH_ENDPOINT', 'https://localhost:9200'),
            'opensearch_username': os.getenv('OPENSEARCH_USERNAME', 'admin'),
            'opensearch_password': os.getenv('OPENSEARCH_PASSWORD', 'password'),
            'aws_region': os.getenv('AWS_REGION', 'us-east-1'),
        }

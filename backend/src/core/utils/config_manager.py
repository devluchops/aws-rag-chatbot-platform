import json
import boto3
import os
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError

class ConfigManager:
    """Manages configuration from SSM Parameter Store and Secrets Manager"""
    
    def __init__(self):
        self.ssm_client = boto3.client('ssm')
        self.secrets_client = boto3.client('secretsmanager')
        self.environment = os.environ.get('ENVIRONMENT', 'dev')
        self.project_name = os.environ.get('PROJECT_NAME', 'aws-chatbot')
        self.ssm_prefix = f"/chatbot/{self.environment}"
        
        # Cache for parameters
        self._cache = {}
        
    def get_parameter(self, parameter_name: str, decrypt: bool = False) -> Optional[str]:
        """Get a single parameter from SSM Parameter Store"""
        full_name = f"{self.ssm_prefix}/{parameter_name}"
        
        # Check cache first
        if full_name in self._cache:
            return self._cache[full_name]
            
        try:
            response = self.ssm_client.get_parameter(
                Name=full_name,
                WithDecryption=decrypt
            )
            value = response['Parameter']['Value']
            self._cache[full_name] = value
            return value
        except ClientError as e:
            if e.response['Error']['Code'] == 'ParameterNotFound':
                print(f"Parameter {full_name} not found")
                return None
            raise
    
    def get_parameters_by_path(self, path: str) -> Dict[str, str]:
        """Get all parameters under a path"""
        full_path = f"{self.ssm_prefix}/{path}"
        
        try:
            response = self.ssm_client.get_parameters_by_path(
                Path=full_path,
                Recursive=True,
                WithDecryption=True
            )
            
            parameters = {}
            for param in response['Parameters']:
                # Remove the prefix to get the relative name
                name = param['Name'].replace(f"{self.ssm_prefix}/", "")
                parameters[name] = param['Value']
            
            return parameters
        except ClientError as e:
            print(f"Error getting parameters by path {full_path}: {e}")
            return {}
    
    def get_secret(self, secret_name: str) -> Optional[Dict[str, Any]]:
        """Get a secret from Secrets Manager"""
        try:
            response = self.secrets_client.get_secret_value(SecretId=secret_name)
            return json.loads(response['SecretString'])
        except ClientError as e:
            print(f"Error getting secret {secret_name}: {e}")
            return None
    
    def get_vpc_config(self) -> Dict[str, Any]:
        """Get VPC configuration"""
        return {
            'vpc_id': self.get_parameter('vpc/id'),
            'subnet_ids': self.get_parameter('vpc/subnet_ids'),
            'security_group_id': self.get_parameter('vpc/security_group_id')
        }
    
    def get_opensearch_config(self) -> Dict[str, Any]:
        """Get OpenSearch configuration"""
        endpoint = self.get_parameter('opensearch/endpoint')
        
        # Get credentials from Secrets Manager
        secret_name = os.environ.get('OPENSEARCH_SECRET_NAME', 
                                   f"{self.project_name}-{self.environment}-opensearch-credentials")
        credentials = self.get_secret(secret_name)
        
        return {
            'endpoint': endpoint,
            'username': credentials.get('username') if credentials else None,
            'password': credentials.get('password') if credentials else None
        }
    
    def get_s3_config(self) -> Dict[str, Any]:
        """Get S3 configuration"""
        return {
            'documents_bucket': self.get_parameter('s3/documents_bucket')
        }
    
    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration at once"""
        config = {
            'environment': self.environment,
            'project_name': self.project_name,
            'vpc': self.get_vpc_config(),
            'opensearch': self.get_opensearch_config(),
            's3': self.get_s3_config()
        }
        
        # Add any additional app-specific parameters
        app_params = self.get_parameters_by_path('app')
        if app_params:
            config['app'] = app_params
            
        return config

# Global instance
config_manager = ConfigManager()

def get_config() -> Dict[str, Any]:
    """Get the current configuration"""
    return config_manager.get_all_config()

def get_opensearch_config() -> Dict[str, Any]:
    """Get OpenSearch configuration"""
    return config_manager.get_opensearch_config()

def get_s3_config() -> Dict[str, Any]:
    """Get S3 configuration"""
    return config_manager.get_s3_config()

def get_vpc_config() -> Dict[str, Any]:
    """Get VPC configuration"""
    return config_manager.get_vpc_config()

import os
import boto3
import json
from typing import Dict, Any, List
from datetime import datetime
import logging

# Importar utilidades
from src.core.utils.environment import get_environment_config, is_lambda_environment
from src.core.utils.service_base import ServiceBase
from services.opensearch_service import OpenSearchService

logger = logging.getLogger(__name__)

class DocumentProcessorService(ServiceBase):
    """Servicio para procesar diferentes tipos de documentos"""
    
    def __init__(self):
        super().__init__()
        
        # Obtener configuración
        config = get_environment_config()
        self.aws_region = config['aws_region']
        
        # Configurar clientes AWS
        self.s3_client = boto3.client('s3', region_name=self.aws_region)
        self.textract_client = boto3.client('textract', region_name=self.aws_region)
        
        # Servicio OpenSearch
        self.opensearch_service = OpenSearchService()
        
        # Tipos de archivo soportados
        self.supported_extensions = {
            '.pdf': self._process_pdf,
            '.txt': self._process_text,
            '.docx': self._process_docx,
            '.md': self._process_markdown
        }
    
    def _process_s3_file_sync(self, bucket: str, key: str) -> Dict[str, Any]:
        """Procesar archivo desde S3 (versión síncrona)"""
        try:
            logger.info(f"Processing file: {key} from bucket: {bucket}")
            
            # Obtener metadata del archivo
            response = self.s3_client.head_object(Bucket=bucket, Key=key)
            file_size = response['ContentLength']
            last_modified = response['LastModified']
            
            # Determinar tipo de archivo
            file_extension = os.path.splitext(key)[1].lower()
            
            if file_extension not in self.supported_extensions:
                raise ValueError(f"Unsupported file type: {file_extension}")
            
            # Procesar según el tipo
            processor = self.supported_extensions[file_extension]
            content = processor(bucket, key)
            
            # Extraer metadata
            metadata = {
                'source': f"s3://{bucket}/{key}",
                'file_size': file_size,
                'last_modified': last_modified.isoformat(),
                'file_type': file_extension,
                'processed_at': datetime.now().isoformat()
            }
            
            # Indexar en OpenSearch
            result = self.opensearch_service._index_document_sync(
                title=os.path.basename(key),
                content=content,
                metadata=metadata
            )
            
            return {
                'document_id': result['_id'],
                'bucket': bucket,
                'key': key,
                'content_length': len(content),
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Error processing file {key}: {str(e)}")
            raise
    
    async def process_s3_file(self, bucket: str, key: str) -> Dict[str, Any]:
        """Procesar archivo desde S3 (versión async)"""
        if self._is_async_context():
            return await self._run_in_executor(self._process_s3_file_sync, bucket, key)
        else:
            return self._process_s3_file_sync(bucket, key)
    
    def _process_direct_document_sync(self, title: str, content: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Procesar documento directo (versión síncrona)"""
        try:
            # Agregar metadata de procesamiento
            proc_metadata = {
                'processed_at': datetime.now().isoformat(),
                'source': 'direct_upload',
                'content_length': len(content)
            }
            
            if metadata:
                proc_metadata.update(metadata)
            
            # Indexar en OpenSearch
            result = self.opensearch_service._index_document_sync(
                title=title,
                content=content,
                metadata=proc_metadata
            )
            
            return {
                'document_id': result['_id'],
                'title': title,
                'content_length': len(content),
                'metadata': proc_metadata
            }
            
        except Exception as e:
            logger.error(f"Error processing direct document: {str(e)}")
            raise
    
    async def process_direct_document(self, title: str, content: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Procesar documento directo (versión async)"""
        if self._is_async_context():
            return await self._run_in_executor(self._process_direct_document_sync, title, content, metadata)
        else:
            return self._process_direct_document_sync(title, content, metadata)
    
    def _process_pdf(self, bucket: str, key: str) -> str:
        """Procesar archivo PDF usando Textract"""
        try:
            # Usar Textract para extraer texto
            response = self.textract_client.detect_document_text(
                Document={
                    'S3Object': {
                        'Bucket': bucket,
                        'Name': key
                    }
                }
            )
            
            # Extraer texto de la respuesta
            text_lines = []
            for item in response['Blocks']:
                if item['BlockType'] == 'LINE':
                    text_lines.append(item['Text'])
            
            return '\n'.join(text_lines)
            
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            # Fallback: descargar y procesar localmente si Textract falla
            return self._download_and_process_text(bucket, key)
    
    def _process_text(self, bucket: str, key: str) -> str:
        """Procesar archivo de texto plano"""
        return self._download_and_process_text(bucket, key)
    
    def _process_docx(self, bucket: str, key: str) -> str:
        """Procesar archivo DOCX"""
        # Por ahora, tratarlo como texto plano
        # En el futuro se puede agregar python-docx
        return self._download_and_process_text(bucket, key)
    
    def _process_markdown(self, bucket: str, key: str) -> str:
        """Procesar archivo Markdown"""
        return self._download_and_process_text(bucket, key)
    
    def _download_and_process_text(self, bucket: str, key: str) -> str:
        """Descargar archivo y procesar como texto"""
        try:
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            content = response['Body'].read()
            
            # Intentar decodificar como UTF-8
            try:
                return content.decode('utf-8')
            except UnicodeDecodeError:
                # Intentar con latin-1 como fallback
                return content.decode('latin-1')
                
        except Exception as e:
            logger.error(f"Error downloading file {key}: {str(e)}")
            raise

import json
import logging
from typing import Dict, Any

# Configurar logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Lambda handler especializado para procesamiento de documentos
    Se usa como función separada para tareas pesadas
    """
    try:
        logger.info(f"Document processor received event: {json.dumps(event, default=str)}")
        
        # Detectar tipo de evento
        if 'Records' in event:
            # S3 Event
            return handle_s3_event(event)
        else:
            # Direct invocation
            return handle_direct_invocation(event)
            
    except Exception as e:
        logger.error(f"Error in document processor: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def handle_s3_event(event) -> Dict[str, Any]:
    """Procesar archivos subidos a S3"""
    from services.document_processor_service import DocumentProcessorService
    
    processor = DocumentProcessorService()
    results = []
    
    for record in event['Records']:
        if record['eventSource'] != 'aws:s3':
            continue
            
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        
        try:
            # Procesar archivo de S3
            result = processor._process_s3_file_sync(bucket, key)
            results.append(result)
            logger.info(f"Successfully processed: {key}")
            
        except Exception as e:
            logger.error(f"Error processing {key}: {str(e)}")
            results.append({
                'bucket': bucket,
                'key': key,
                'error': str(e)
            })
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f'Processed {len(results)} documents',
            'results': results
        }, default=str)
    }

def handle_direct_invocation(event) -> Dict[str, Any]:
    """Procesar documentos enviados directamente"""
    from services.document_processor_service import DocumentProcessorService
    
    processor = DocumentProcessorService()
    
    # Parsear cuerpo del evento
    if 'body' in event:
        body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
    else:
        body = event
    
    # Validar entrada
    if not body.get('title') or not body.get('content'):
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'title and content are required'})
        }
    
    try:
        # Procesar documento
        result = processor._process_direct_document_sync(
            title=body['title'],
            content=body['content'],
            metadata=body.get('metadata', {})
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Document processed successfully',
                'document_id': result['document_id']
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

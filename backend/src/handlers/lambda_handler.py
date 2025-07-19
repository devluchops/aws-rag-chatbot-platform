from mangum import Mangum
from src.api.main import app

# Envolver FastAPI app para Lambda
handler = Mangum(app, lifespan="off")

def lambda_handler(event, context):
    """AWS Lambda handler"""
    return handler(event, context)

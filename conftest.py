"""Configuração global do pytest - Carregado antes de qualquer teste"""
import os

# Configurar variáveis de ambiente AWS ANTES de qualquer import de módulos
# Isso é executado antes da coleta de testes
def pytest_configure(config):
    """Hook do pytest executado antes da coleta de testes"""
    os.environ.setdefault('AWS_REGION', 'us-east-1')
    os.environ.setdefault('AWS_ACCOUNT_ID', '123456789012')
    os.environ.setdefault('S3_BUCKET_NAME', 'test-bucket')
    os.environ.setdefault('DYNAMODB_TABLE_NAME', 'TestVideoSlice')
    os.environ.setdefault('SQS_URL', 'https://sqs.us-east-1.amazonaws.com/test')
    os.environ.setdefault('EVENT_BUS_NAME', 'test-event-bus')
    os.environ.setdefault('PNG_COMPRESSION_LEVEL', '9')
    os.environ.setdefault('ZIP_COMPRESSION_LEVEL', '5')
    os.environ.setdefault('VDSC_QUALITY', '{"ultra": 1080, "high": 720, "medium": 480, "low": 360}')

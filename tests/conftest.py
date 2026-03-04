"""Configuração global do pytest - Carregado antes de qualquer teste"""
import os
import sys
from pathlib import Path

# Adicionar src ao sys.path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

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
    os.environ.setdefault('VDSC_RESIZE', '{"ultra": 1080, "high": 720, "medium": 480, "low": 360}')
    os.environ.setdefault('SCHEDULE_EVENT_RETRY_BACKOFF_FACTOR', '5')
    os.environ.setdefault('SCHEDULE_TARGET_ARN', 'arn:aws:sqs:us-east-1:080145351546:vdsc-prd-sqs-video-slice')
    os.environ.setdefault('SCHEDULE_EVENT_ROLE_ARN', 'arn:aws:iam::080145351546:role/vdsc-prd-schduler-role')
    os.environ.setdefault('SCHEDULE_EVENT_DLQ', 'arn:aws:sqs:us-east-1:080145351546:vdsc-prd-sqs-video-slice-dlq')




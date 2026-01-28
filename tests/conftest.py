"""Configurações e fixtures compartilhadas para os testes"""
import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock

# Mock do decorador idempotent antes de qualquer import do app
def mock_idempotent_decorator(config=None, persistence_layer=None, **kwargs):
    """Mock do decorador idempotent que apenas passa através da função"""
    def decorator(func):
        return func
    return decorator

# Mock das classes de configuração de idempotência
mock_idempotency_module = MagicMock()
mock_idempotency_module.idempotent = mock_idempotent_decorator
mock_idempotency_module.IdempotencyConfig = MagicMock
mock_idempotency_module.DynamoDBPersistenceLayer = MagicMock

sys.modules['aws_lambda_powertools.utilities.idempotency'] = mock_idempotency_module

# Adiciona o diretório src ao path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture(scope="session")
def test_data_dir():
    """Retorna o diretório de dados de teste"""
    return Path(__file__).parent / "data"


@pytest.fixture
def mock_aws_env(monkeypatch):
    """Fixture para configurar variáveis de ambiente AWS para testes"""
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("AWS_ACCOUNT_ID", "123456789012")
    monkeypatch.setenv("S3_BUCKET_NAME", "test-bucket")
    monkeypatch.setenv("DYNAMODB_TABLE_NAME", "TestVideoSlice")
    monkeypatch.setenv("SQS_URL", "https://sqs.us-east-1.amazonaws.com/test")
    monkeypatch.setenv("EVENT_BUS_NAME", "test-event-bus")
    monkeypatch.setenv("PNG_COMPRESSION_LEVEL", "9")
    monkeypatch.setenv("ZIP_COMPRESSION_LEVEL", "5")

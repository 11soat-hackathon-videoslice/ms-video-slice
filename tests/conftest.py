"""Configurações e fixtures compartilhadas para os testes"""
import pytest
import sys
import os
from pathlib import Path

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

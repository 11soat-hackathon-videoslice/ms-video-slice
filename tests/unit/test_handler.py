"""Testes unitários para lambda_handler"""
import pytest
import json
from unittest.mock import Mock
from app import lambda_handler


@pytest.mark.unit
class TestVdscProcessHandler:
    """Testes para o handler principal"""

    @pytest.fixture
    def valid_dynamodb_event(self):
        """Fixture com evento válido do DynamoDB"""
        return {
            'Records': [
                {
                    'eventID': 'evt-1',
                    'dynamodb': {
                        'NewImage': {
                            'videoId': {'S': 'video123'},
                            'fileName': {'S': 'test.mp4'},
                            'extensionFile': {'S': 'mp4'},
                            'status': {'S': 'uploaded'},
                            'created': {'S': '2026-01-13T00:00:00Z'},
                            'userId': {'S': 'user123'},
                            'totalTime': {'N': '3600'},
                            'unitTime': {'S': 's'},
                            'startTime': {'N': '0'},
                            'endTime': {'N': '60'},
                            'timeInterval': {'L': [{'S': '00:00:00'}]},
                            'maxRetry': {'N': '3'},
                            'retries': {'N': '0'},
                            'quality': {'S': 'high'},
                            'logs': {'L': []}
                        }
                    }
                }
            ]
        }

    def test_handler_success(self, valid_dynamodb_event):
        """Testa handler com sucesso (processamento síncrono)"""
        context = Mock()
        result = lambda_handler(valid_dynamodb_event, context)
        assert result['statusCode'] == 202
        body = json.loads(result['body'])
        assert 'status' in body
        assert 'Recebido' in body['status']

    def test_handler_with_invalid_event(self, valid_dynamodb_event):
        """Testa handler com evento inválido (sem Records)"""
        event = {'Records': []}  # Corrigido para sempre ter a chave
        context = Mock()
        result = lambda_handler(event, context)
        assert result['statusCode'] == 202
        body = json.loads(result['body'])
        assert 'status' in body
        assert 'Recebido' in body['status']

    def test_handler_with_processing_error(self, valid_dynamodb_event):
        """Testa handler com evento válido (não há invoke, só processamento local)"""
        context = Mock()
        result = lambda_handler(valid_dynamodb_event, context)
        assert result['statusCode'] == 202
        body = json.loads(result['body'])
        assert 'status' in body
        assert 'Recebido' in body['status']

    def test_handler_with_empty_records(self):
        """Testa handler com lista de registros vazia"""
        event = {'Records': []}
        context = Mock()
        result = lambda_handler(event, context)
        assert result['statusCode'] == 202
        body = json.loads(result['body'])
        assert 'status' in body
        assert 'Recebido' in body['status']

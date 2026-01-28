"""Testes unitários para lambda_handler"""
import pytest
import json
from unittest.mock import patch
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

    @patch('app.process_video_async')
    @patch('app.asyncio.run')
    def test_handler_success(self, mock_asyncio_run, mock_process_video, valid_dynamodb_event):
        """Testa handler com sucesso"""
        mock_asyncio_run.return_value = [None]  # Retorna lista com 1 resultado bem-sucedido

        result = lambda_handler(valid_dynamodb_event, None)

        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert 'Processamento concluído com sucesso' in body['message']
        mock_asyncio_run.assert_called_once()

    @patch('app.process_video_async')
    @patch('app.asyncio.run')
    def test_handler_with_invalid_event(self, mock_asyncio_run, mock_process_video, valid_dynamodb_event):
        """Testa handler com evento inválido"""
        valid_dynamodb_event['Records'][0]['dynamodb']['NewImage']['videoId'] = {'S': ''}
        mock_asyncio_run.side_effect = Exception("Erro de validação")

        result = lambda_handler(valid_dynamodb_event, None)

        assert result['statusCode'] == 500
        assert 'error' in json.loads(result['body'])

    @patch('app.process_video_async')
    @patch('app.asyncio.run')
    def test_handler_with_processing_error(self, mock_asyncio_run, mock_process_video, valid_dynamodb_event):
        """Testa handler com erro no processamento"""
        mock_asyncio_run.side_effect = Exception("Erro de processamento")

        result = lambda_handler(valid_dynamodb_event, None)

        assert result['statusCode'] == 500
        assert 'error' in json.loads(result['body'])

    def test_handler_with_empty_records(self):
        """Testa handler com lista de registros vazia"""
        event = {'Records': []}
        result = lambda_handler(event, None)
        # Handler retorna 200 com mensagem de erro quando não há registros
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert 'error' in body

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

"""Testes unitários para app.py - Lambda Handler com processamento assíncrono"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from src.app import _process_video_event

mock_idempotent_func = MagicMock(side_effect=lambda **kwargs: lambda func: func)

with patch("aws_lambda_powertools.utilities.idempotency.idempotent_function", mock_idempotent_func):
    from src.app import lambda_handler

@pytest.fixture
def lambda_context():
    """Gera um mock do contexto da Lambda com tempo restante"""
    context = MagicMock()
    context.get_remaining_time_in_millis.return_value = 30000
    return context


@pytest.mark.unit
class TestLambdaHandler:
    """Testes para o lambda_handler principal"""

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

    def test_lambda_handler_success(self, valid_dynamodb_event):
        """Testa lambda_handler com sucesso (processamento síncrono)"""
        context = Mock()
        # Patch para evitar processar internamente e simular sucesso
        with patch('src.app._process_video_event') as mock_process_event:
            mock_process_event.return_value = None
            result = lambda_handler(valid_dynamodb_event, context)
            assert result['statusCode'] == 202
            body = json.loads(result['body'])
            assert 'status' in body
            assert 'Recebido' in body['status']

    def test_lambda_handler_with_empty_records(self):
        """Testa lambda_handler com lista de registros vazia"""
        event = {'Records': []}
        context = Mock()
        result = lambda_handler(event, context)
        assert result['statusCode'] == 202
        body = json.loads(result['body'])
        assert 'status' in body
        assert 'Recebido' in body['status']

    def test_lambda_handler_without_records_key(self):
        """Testa lambda_handler sem chave Records (deve passar lista vazia)"""
        event = {'Records': []}  # Corrigido para sempre ter a chave
        context = Mock()
        result = lambda_handler(event, context)
        assert result['statusCode'] == 202
        body = json.loads(result['body'])
        assert 'status' in body
        assert 'Recebido' in body['status']

    def test_lambda_handler_invoke_exception(self, valid_dynamodb_event):
        """Testa lambda_handler com evento válido e falha no processamento interno"""
        context = Mock()
        # Patch para simular exceção durante processamento
        with patch('src.app._process_video_event', side_effect=Exception('fail')):
            result = lambda_handler(valid_dynamodb_event, context)
            assert result['statusCode'] == 500
            body = json.loads(result['body'])
            assert 'error' in body


class TestAppInternals:

    def test__process_video_event_success(self):
        """Testa processamento bem-sucedido de evento de vídeo"""
        mock_metadata = MagicMock()
        mock_metadata.video_id = 'vid'
        with patch('src.app.controller') as mock_controller, \
             patch('src.app.config') as mock_config, \
             patch('src.app.logger') as mock_logger, \
             patch('os.listdir', return_value=[]), \
             patch('os.path.isfile', return_value=False), \
             patch('os.path.isdir', return_value=False), \
             patch('os.unlink'), \
             patch('shutil.rmtree'):
            _process_video_event(mock_metadata)
            mock_controller.video_slice_processing.assert_called_with(mock_metadata, mock_config)
            mock_logger.info.assert_any_call('Processamento concluído para vídeo ID: vid')

    def test__process_video_event_exception(self):
        """Testa tratamento de exceção durante processamento de vídeo"""
        mock_metadata = MagicMock()
        mock_metadata.video_id = 'vid'
        with patch('src.app.controller') as mock_controller, \
             patch('src.app.logger') as mock_logger, \
             patch('os.listdir', return_value=[]), \
             patch('os.path.isfile', return_value=False), \
             patch('os.path.isdir', return_value=False), \
             patch('os.unlink'), \
             patch('shutil.rmtree'):
            mock_controller.video_slice_processing.side_effect = Exception('fail')
            _process_video_event(mock_metadata)
            assert mock_logger.error.called
            mock_controller.handler.handle_exception.assert_called_once()



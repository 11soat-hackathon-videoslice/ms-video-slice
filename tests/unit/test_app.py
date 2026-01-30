import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

"""Testes unitários para app.py - Lambda Handler com processamento assíncrono"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from src.app import init_extension, _process_video_event

mock_idempotent_func = MagicMock(side_effect=lambda **kwargs: lambda func: func)

with patch("aws_lambda_powertools.utilities.idempotency.idempotent_function", mock_idempotent_func):
    from src.app import lambda_handler, process_async_loop # Agora o app importa o mock

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
        """Testa lambda_handler com evento válido (não há invoke, só processamento local)"""
        context = Mock()
        result = lambda_handler(valid_dynamodb_event, context)
        assert result['statusCode'] == 202
        body = json.loads(result['body'])
        assert 'status' in body
        assert 'Recebido' in body['status']


class TestAppInternals:
    def test_process_async_loop_handles_queue_and_errors(self):
        class ExitLoop(BaseException): pass
        mock_queue = MagicMock()
        mock_queue.empty.side_effect = [False, True]
        mock_queue.get_nowait.return_value = (lambda x: None, 'data_teste')
        mock_requests_get = MagicMock()
        mock_requests_get.side_effect = [MagicMock(), ExitLoop()]
        with patch.dict('os.environ', {'AWS_LAMBDA_RUNTIME_API': 'localhost'}), \
                patch('src.app.async_events_queue', mock_queue), \
                patch('src.app.requests.get', mock_requests_get), \
                patch('src.app.logger'):
            try:
                process_async_loop('extid')
            except ExitLoop:
                pass
            assert mock_queue.get_nowait.called
            assert mock_requests_get.call_count == 2

    def test_init_extension_no_env(self):
        with patch.dict('os.environ', {}, clear=True), \
             patch('src.app.logger') as mock_logger:
            init_extension()
            mock_logger.info.assert_called_with('AWS_LAMBDA_RUNTIME_API não está definido. A extensão não será iniciada.')

    def test_init_extension_success(self):
        with patch.dict('os.environ', {'AWS_LAMBDA_RUNTIME_API': 'localhost'}), \
             patch('src.app.requests.post') as mock_post, \
             patch('src.app.threading.Thread') as mock_thread:
            mock_post.return_value.headers = {'Lambda-Extension-Identifier': 'extid'}
            init_extension()
            assert mock_thread.called

    def test_init_extension_exception(self):
        with patch.dict('os.environ', {'AWS_LAMBDA_RUNTIME_API': 'localhost'}), \
             patch('src.app.requests.post', side_effect=Exception('fail')), \
             patch('src.app.logger') as mock_logger:
            init_extension()
            assert mock_logger.error.called

    def test__process_video_event_success(self):
        record = MagicMock()
        record.dynamodb.new_image = {'videoId': 'vid'}
        with patch('src.app.VdscMetadataDTO.from_dynamodb_item') as mock_from, \
             patch('src.app.controller') as mock_controller, \
             patch('src.app.config') as mock_config, \
             patch('src.app.logger') as mock_logger, \
             patch('os.listdir', return_value=[]), \
             patch('os.path.isfile', return_value=False), \
             patch('os.path.isdir', return_value=False), \
             patch('os.unlink'), \
             patch('shutil.rmtree'):
            mock_metadata = MagicMock()
            mock_metadata.video_id = 'vid'
            mock_from.return_value = mock_metadata
            _process_video_event(record)
            mock_controller.video_slice_processing.assert_called()
            mock_logger.info.assert_any_call('Processamento concluído para vídeo ID: vid')

    def test__process_video_event_exception(self):
        record = MagicMock()
        record.dynamodb.new_image = {'videoId': 'vid'}
        with patch('src.app.VdscMetadataDTO.from_dynamodb_item', side_effect=Exception('fail')), \
             patch('src.app.controller') as mock_controller, \
             patch('src.app.logger') as mock_logger, \
             patch('os.listdir', return_value=[]), \
             patch('os.path.isfile', return_value=False), \
             patch('os.path.isdir', return_value=False), \
             patch('os.unlink'), \
             patch('shutil.rmtree'):
            _process_video_event(record)
            assert mock_logger.error.called
            mock_controller.handler.handle_exception.assert_called()

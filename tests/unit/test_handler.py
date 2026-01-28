"""Testes unitários para vdsc_process_handler"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from src.aws.handler.vdsc_process_handler import lambda_handler


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

    @patch('src.aws.handler.vdsc_process_handler.VdscController')
    @patch('src.aws.handler.vdsc_process_handler.VdscDataProxy')
    def test_handler_success(self, mock_dataproxy_class, mock_controller_class, valid_dynamodb_event):
        """Testa handler com sucesso"""
        mock_controller = Mock()
        mock_controller_class.return_value = mock_controller

        result = lambda_handler(valid_dynamodb_event, None)

        # Handler não retorna nada em caso de sucesso
        mock_controller.video_slice_processing.assert_called_once()

    @patch('src.aws.handler.vdsc_process_handler.VdscController')
    def test_handler_with_invalid_event(self, mock_controller_class, valid_dynamodb_event):
        """Testa handler com evento inválido"""
        valid_dynamodb_event['Records'][0]['dynamodb']['NewImage']['videoId'] = {'S': ''}

        result = lambda_handler(valid_dynamodb_event, None)

        assert result['statusCode'] == 500
        assert 'error' in json.loads(result['body'])

    @patch('src.aws.handler.vdsc_process_handler.VdscController')
    def test_handler_with_processing_error(self, mock_controller_class, valid_dynamodb_event):
        """Testa handler com erro no processamento"""
        mock_controller = Mock()
        mock_controller_class.return_value = mock_controller
        mock_controller.video_slice_processing.side_effect = Exception("Erro de processamento")

        result = lambda_handler(valid_dynamodb_event, None)

        assert result['statusCode'] == 500
        assert 'error' in json.loads(result['body'])

    def test_handler_with_empty_records(self):
        """Testa handler com lista de registros vazia"""
        event = {'Records': []}
        result = lambda_handler(event, None)
        # Handler não deve retornar erro se não há registros
        assert result is None or result.get('statusCode') != 500

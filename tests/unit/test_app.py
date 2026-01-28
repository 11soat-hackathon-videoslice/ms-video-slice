"""Testes unitários para app.py - Lambda Handler com processamento assíncrono"""
import pytest
import json
from unittest.mock import Mock, patch
from app import lambda_handler, process_video_async


@pytest.mark.unit
class TestLambdaHandler:
    """Testes para o lambda_handler principal"""

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
    def test_lambda_handler_success(self, mock_asyncio_run, mock_process_video, valid_dynamodb_event):
        """Testa lambda_handler com sucesso"""
        mock_asyncio_run.return_value = [None]  # Retorna lista com 1 resultado bem-sucedido

        result = lambda_handler(valid_dynamodb_event, None)

        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert 'Processamento concluído com sucesso' in body['message']
        mock_asyncio_run.assert_called_once()

    def test_lambda_handler_with_empty_records(self):
        """Testa lambda_handler com lista de registros vazia"""
        event = {'Records': []}

        result = lambda_handler(event, None)

        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert 'error' in body
        assert 'Registro vazio' in body['error']

    def test_lambda_handler_without_records_key(self):
        """Testa lambda_handler sem chave Records"""
        event = {}

        result = lambda_handler(event, None)

        assert result['statusCode'] == 500
        body = json.loads(result['body'])
        assert 'error' in body

    @patch('app.process_video_async')
    @patch('app.asyncio.run')
    def test_lambda_handler_with_timeout_error(self, mock_asyncio_run, mock_process_video, valid_dynamodb_event):
        """Testa lambda_handler quando ocorre timeout"""
        import asyncio
        mock_asyncio_run.side_effect = asyncio.TimeoutError()

        result = lambda_handler(valid_dynamodb_event, None)

        assert result['statusCode'] == 408
        body = json.loads(result['body'])
        assert 'Timeout' in body['error']

    @patch('app.process_video_async')
    @patch('app.asyncio.run')
    def test_lambda_handler_with_generic_exception(self, mock_asyncio_run, mock_process_video, valid_dynamodb_event):
        """Testa lambda_handler com exceção genérica"""
        mock_asyncio_run.side_effect = Exception("Erro inesperado no processamento")

        result = lambda_handler(valid_dynamodb_event, None)

        assert result['statusCode'] == 500
        body = json.loads(result['body'])
        assert 'error' in body

    @patch('app.process_video_async')
    @patch('app.asyncio.run')
    def test_lambda_handler_logs_event(self, mock_asyncio_run, mock_process_video, valid_dynamodb_event, caplog):
        """Testa se o handler registra o evento recebido nos logs"""
        mock_asyncio_run.return_value = [None]

        with caplog.at_level('INFO'):
            lambda_handler(valid_dynamodb_event, None)

        assert "Recebido evento do DynamoDB" in caplog.text


@pytest.mark.unit
class TestProcessVideoAsync:
    """Testes para process_video_async"""

    @pytest.fixture
    def mock_event_dto(self):
        """Fixture com DTO de evento mockado"""
        dto = Mock()
        dto.video_id = 'video123'
        dto.file_name = 'test.mp4'
        dto.validate.return_value = None
        return dto

    @patch('app.VdscController')
    @patch('app.VdscDataProxy')
    @patch('app.dynamodb_repository')
    @patch('app.s3_repository')
    @patch('app.event_producer')
    def test_process_video_async_success(
        self,
        mock_event_prod,
        mock_s3_repo,
        mock_dynamo_repo,
        mock_dataproxy_class,
        mock_controller_class,
        mock_event_dto
    ):
        """Testa processamento assíncrono de vídeo com sucesso"""
        mock_dataproxy = Mock()
        mock_dataproxy_class.return_value = mock_dataproxy

        mock_controller = Mock()
        mock_controller_class.return_value = mock_controller
        mock_controller.video_slice_processing.return_value = None

        # Executar função
        process_video_async(mock_event_dto)

        # Verificar chamadas
        mock_dataproxy_class.assert_called_once()
        mock_controller_class.assert_called_once()
        mock_controller.video_slice_processing.assert_called_once()

    @patch('app.VdscController')
    @patch('app.VdscDataProxy')
    def test_process_video_async_with_error(self, mock_dataproxy_class, mock_controller_class, mock_event_dto, caplog):
        """Testa processamento assíncrono quando ocorre erro"""
        mock_controller = Mock()
        mock_controller_class.return_value = mock_controller
        mock_controller.video_slice_processing.side_effect = Exception("Erro no processamento do vídeo")

        # Agora deve lançar exceção já que fizemos raise
        with pytest.raises(Exception, match="Erro no processamento do vídeo"):
            process_video_async(mock_event_dto)

        assert "Erro ao processar vídeo" in caplog.text
        assert mock_event_dto.video_id in caplog.text

    @patch('app.VdscController')
    @patch('app.VdscDataProxy')
    def test_process_video_async_logs_completion(self, mock_dataproxy_class, mock_controller_class, mock_event_dto, caplog):
        """Testa se o processamento registra conclusão nos logs"""
        mock_controller = Mock()
        mock_controller_class.return_value = mock_controller

        with caplog.at_level('INFO'):
            process_video_async(mock_event_dto)

        assert "Processamento concluído para vídeo ID" in caplog.text
        assert mock_event_dto.video_id in caplog.text


@pytest.mark.unit
class TestConfiguration:
    """Testes para verificar configuração do módulo"""

    def test_executor_is_configured(self):
        """Testa se o ThreadPoolExecutor está configurado"""
        from app import executor
        assert executor is not None
        assert executor._max_workers >= 1

    def test_config_initialization(self):
        """Testa se a configuração é inicializada"""
        from app import config
        assert config is not None
        assert hasattr(config, 'vdsc')
        assert 'max_workers' in config.vdsc
        assert 'max_timeout' in config.vdsc

    def test_logging_is_configured(self):
        """Testa se o logging está configurado"""
        from app import logger
        assert logger is not None
        assert logger.name == 'app'

    def test_repositories_are_initialized(self):
        """Testa se os repositórios são inicializados"""
        from app import dynamodb_repository, s3_repository, event_producer
        assert dynamodb_repository is not None
        assert s3_repository is not None
        assert event_producer is not None


@pytest.mark.unit
class TestIntegrationScenarios:
    """Testes de cenários de integração"""

    @pytest.fixture
    def multiple_records_event(self):
        """Fixture com múltiplos registros"""
        return {
            'Records': [
                {
                    'dynamodb': {
                        'NewImage': {
                            'videoId': {'S': f'video{i}'},
                            'fileName': {'S': f'test{i}.mp4'},
                            'extensionFile': {'S': 'mp4'},
                            'status': {'S': 'uploaded'},
                            'created': {'S': '2026-01-13T00:00:00Z'},
                            'userId': {'S': f'user{i}'},
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
                for i in range(3)
            ]
        }

    @patch('app.process_video_async')
    @patch('app.asyncio.run')
    def test_lambda_handler_with_multiple_records(self, mock_asyncio_run, mock_process_video, multiple_records_event):
        """Testa lambda_handler com múltiplos registros"""
        mock_asyncio_run.return_value = [None, None, None]  # 3 resultados bem-sucedidos

        result = lambda_handler(multiple_records_event, None)

        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert 'Processamento concluído com sucesso para 3 vídeo(s)' in body['message']

    @patch('app.process_video_async')
    @patch('app.asyncio.run')
    def test_lambda_handler_returns_json_response(self, mock_asyncio_run, mock_process_video, multiple_records_event):
        """Testa se o handler retorna resposta JSON válida"""
        mock_asyncio_run.return_value = [None, None, None]  # 3 resultados bem-sucedidos

        result = lambda_handler(multiple_records_event, None)

        assert 'statusCode' in result
        assert 'body' in result
        # Verificar se o body é JSON válido
        body = json.loads(result['body'])
        assert 'message' in body

import os

import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

"""Testes unitários para app.py - Lambda Handler com processamento assíncrono"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from src.app import _process_video_event

mock_idempotent_func = MagicMock(side_effect=lambda **kwargs: lambda func: func)
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
        """Fixture com evento válido do DynamoDB do arquivo sqs_insert_event.json"""
        return {
            "Records": [
                {
                    "messageId": "b22abd8b-bc65-49ac-ac27-35cb0c8f4e25",
                    "receiptHandle": "AQEBiFJ77Y0/+3PQMeBB8kYsgZmx3QZ/1bXXAIfv5qQkwvWjYZXmp1QDWAJAcyCD/ZUAu7FLKoVVRSfJEkKxhqUq4Uw5qX0Ac4PgEmGd45e6v+aMSZzoLA3HFjHi+gJYGI/89EXb51c2xlZZ0fjf8wkAl+oRZnecdBt7r/3/2QpbjhnGwt/I5ffOGgn4vCgPy+E2GvH7RV01TidGoiyxwq47M7I1tkHIaZmZIOw3PyufwSh7zFUQsmXyDb2+0vTGgkTT5yjePJI14uJTCGVvopZ8cUDQ/Qgd3eNxskkBTmWscRX/bHSyzLpNxDJ0IXbamvDk296J/5TvEA1pRNQnd41T6XgGUq3Jx0nKmmWdled/T0E3Q8IZx66eiIkp0Lvfi9UiRnDlIIkv3/WnVB4DfYr4rQ==",
                    "body": {
                        "version": "0",
                        "id": "5653c908-f4da-35c2-c68a-5a25febebd7d",
                        "detail-type": "Event from aws:dynamodb",
                        "source": "vdsc.pipe",
                        "account": "080145351546",
                        "time": "2026-02-05T14:25:06Z",
                        "region": "us-east-1",
                        "resources": [],
                        "detail": {
                            "eventID": "d05b753a5dbd8f0ea74593e9aece815f",
                            "eventName": "INSERT",
                            "eventVersion": "1.1",
                            "eventSource": "aws:dynamodb",
                            "awsRegion": "us-east-1",
                            "dynamodb": {
                                "ApproximateCreationDateTime": 1770301506,
                                "Keys": {
                                    "videoId": {
                                        "S": "ml9jexx5TWrC"
                                    }
                                },
                                "NewImage": {
                                    "fileName": {
                                        "S": "2024-07-25_16-47-46"
                                    },
                                    "created": {
                                        "S": "2026-02-05 11:14:16"
                                    },
                                    "totalTime": {
                                        "N": "4"
                                    },
                                    "videoId": {
                                        "S": "ml9jexx5TWrC"
                                    },
                                    "userId": {
                                        "S": "848834a8-20e1-7004-ee3b-4ba1495239d8"
                                    },
                                    "resize": {
                                        "S": "medium"
                                    },
                                    "maxRetries": {
                                        "N": "3"
                                    },
                                    "retries": {
                                        "N": "0"
                                    },
                                    "fileExtension": {
                                        "S": "mp4"
                                    },
                                    "intervalTime": {
                                        "L": [
                                            {
                                                "S": "1"
                                            }
                                        ]
                                    },
                                    "startTime": {
                                        "N": "0"
                                    },
                                    "endTime": {
                                        "N": "4"
                                    },
                                    "status": {
                                        "S": "UPLOADED"
                                    },
                                    "unitTime": {
                                        "S": "s"
                                    },
                                    "qualityOutputLevel": {
                                        "N": "50"
                                    }
                                },
                                "SequenceNumber": "102042700003665459637771224",
                                "SizeBytes": 250,
                                "StreamViewType": "NEW_AND_OLD_IMAGES"
                            },
                            "eventSourceARN": "arn:aws:dynamodb:us-east-1:080145351546:table/VideoSlice/stream/2026-01-26T20:20:36.322"
                        }
                    },
                    "attributes": {
                        "ApproximateReceiveCount": "1",
                        "SentTimestamp": "1770301506645",
                        "SenderId": "AROARFKIJAN5FITLMQ6SR:0ae57debe57431e69bbf0909913a2646",
                        "ApproximateFirstReceiveTimestamp": "1770301506652"
                    },
                    "messageAttributes": {},
                    "md5OfMessageAttributes": None,
                    "md5OfBody": "f406634cb996416eb193d84c19842dfe",
                    "eventSource": "aws:sqs",
                    "eventSourceARN": "arn:aws:sqs:us-east-1:080145351546:vdsc-prd-sqs-video-slice",
                    "awsRegion": "us-east-1"
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
            with pytest.raises(Exception, match='fail'):
                lambda_handler(valid_dynamodb_event, context)

    def test_lambda_handler_with_sqs_event(self):
        """Testa lambda_handler com evento vindo do SQS (body como string JSON)"""
        context = Mock()
        dynamodb_payload = {
            'videoId': {'S': 'video123'},
            'fileName': {'S': 'test.mp4'},
            'fileExtension': {'S': 'mp4'},
            'status': {'S': 'uploaded'},
            'created': {'S': '2026-01-13T00:00:00Z'},
            'userId': {'S': 'user123'},
            'totalTime': {'N': '3600'},
            'unitTime': {'S': 's'},
            'startTime': {'N': '0'},
            'endTime': {'N': '60'},
            'intervalTime': {'L': [{'S': '00:00:00'}]},
            'maxRetries': {'N': '3'},
            'retries': {'N': '0'},
            'resize': {'S': 'high'},
            'qualityOutputLevel': {'N': '80'},
            'logs': {'L': []}
        }

        sqs_event = {
            'Records': [
                {
                    'messageId': 'msg123',
                    'body': json.dumps({
                        'detail': {
                            'dynamodb': {
                                'NewImage': dynamodb_payload
                            }
                        }
                    })
                }
            ]
        }

        with patch('src.app._process_video_event') as mock_process_event:
            mock_process_event.return_value = None
            result = lambda_handler(sqs_event, context)
            assert result['statusCode'] == 202
            body = json.loads(result['body'])
            assert 'status' in body
            mock_process_event.assert_called_once()

    def test_lambda_handler_with_invalid_sqs_event(self):
        """Testa lambda_handler com evento SQS que não contém NewImage"""
        context = Mock()
        sqs_event = {
            'Records': [
                {
                    'messageId': 'msg123',
                    'body': json.dumps({
                        'detail': {
                            'dynamodb': {}
                        }
                    })
                }
            ]
        }

        with pytest.raises(Exception):
            lambda_handler(sqs_event, context)


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
            with pytest.raises(Exception, match='fail'):
                _process_video_event(mock_metadata)
            mock_logger.error.assert_called()

    def test__process_video_event_with_cleanup(self):
        """Testa processamento com limpeza de arquivos temporários"""
        mock_metadata = MagicMock()
        mock_metadata.video_id = 'vid123'

        # Simular retorno de listdir com arquivos
        files_to_clean = ['file1.tmp', 'file2.tmp']

        with patch('src.app.controller') as mock_controller, \
             patch('src.app.config') as mock_config, \
             patch('src.app.logger') as mock_logger, \
             patch('os.path.isdir', return_value=True), \
             patch('os.listdir', return_value=files_to_clean), \
             patch('os.path.isfile', return_value=True), \
             patch('os.unlink') as mock_unlink, \
             patch('shutil.rmtree') as mock_rmtree:

            _process_video_event(mock_metadata)

            # Valida que tentou limpar os arquivos
            assert mock_unlink.called
            mock_logger.info.assert_any_call('Processamento concluído para vídeo ID: vid123')

    def test__process_video_event_cleanup_error(self):
        """Testa limpeza de filesystem mesmo com erro"""
        mock_metadata = MagicMock()
        mock_metadata.video_id = 'vid456'

        with patch('src.app.controller') as mock_controller, \
             patch('src.app.logger') as mock_logger, \
             patch('os.listdir', return_value=[]) as mock_listdir, \
             patch('os.path.isfile', return_value=False), \
             patch('os.path.isdir', return_value=False), \
             patch('os.unlink') as mock_unlink, \
             patch('shutil.rmtree') as mock_rmtree:

            mock_controller.video_slice_processing.side_effect = Exception('processing error')
            with pytest.raises(Exception, match='processing error'):
                _process_video_event(mock_metadata)

            # Valida que tentou limpar mesmo com erro
            mock_logger.error.assert_called()



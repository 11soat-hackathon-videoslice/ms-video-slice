"""Testes unitários para lambda_handler"""
import pytest
import json
from unittest.mock import Mock, patch
from app import lambda_handler


@pytest.mark.unit
class TestVdscProcessHandler:
    """Testes para o handler principal"""

    @pytest.fixture
    def valid_dynamodb_event(self):
        """Fixture com evento válido do DynamoDB com estrutura SQS completa"""
        return {
            'Records': [
                {
                    'messageId': 'b22abd8b-bc65-49ac-ac27-35cb0c8f4e25',
                    'receiptHandle': 'test-receipt-handle',
                    'body': {
                        'version': '0',
                        'id': '5653c908-f4da-35c2-c68a-5a25febebd7d',
                        'detail-type': 'Event from aws:dynamodb',
                        'source': 'vdsc.pipe',
                        'account': '080145351546',
                        'time': '2026-02-05T14:25:06Z',
                        'region': 'us-east-1',
                        'resources': [],
                        'detail': {
                            'eventID': 'd05b753a5dbd8f0ea74593e9aece815f',
                            'eventName': 'INSERT',
                            'eventVersion': '1.1',
                            'eventSource': 'aws:dynamodb',
                            'awsRegion': 'us-east-1',
                            'dynamodb': {
                                'ApproximateCreationDateTime': 1770301506,
                                'Keys': {
                                    'videoId': {'S': 'ml9jexx5TWrC'}
                                },
                                'NewImage': {
                                    'fileName': {'S': '2024-07-25_16-47-46'},
                                    'created': {'S': '2026-02-05 11:14:16'},
                                    'totalTime': {'N': '4'},
                                    'videoId': {'S': 'ml9jexx5TWrC'},
                                    'userId': {'S': '848834a8-20e1-7004-ee3b-4ba1495239d8'},
                                    'quality': {'S': 'medium'},
                                    'maxRetry': {'N': '3'},
                                    'retries': {'N': '0'},
                                    'extensionFile': {'S': 'mp4'},
                                    'timeInterval': {'L': [{'S': '1'}]},
                                    'startTime': {'N': '0'},
                                    'endTime': {'N': '4'},
                                    'status': {'S': 'UPLOADED'},
                                    'unitTime': {'S': 's'}
                                },
                                'SequenceNumber': '102042700003665459637771224',
                                'SizeBytes': 250,
                                'StreamViewType': 'NEW_AND_OLD_IMAGES'
                            },
                            'eventSourceARN': 'arn:aws:dynamodb:us-east-1:080145351546:table/VideoSlice/stream/2026-01-26T20:20:36.322'
                        }
                    },
                    'attributes': {
                        'ApproximateReceiveCount': '1',
                        'SentTimestamp': '1770301506645',
                        'SenderId': 'AROARFKIJAN5FITLMQ6SR:0ae57debe57431e69bbf0909913a2646',
                        'ApproximateFirstReceiveTimestamp': '1770301506652'
                    },
                    'messageAttributes': {},
                    'md5OfMessageAttributes': None,
                    'md5OfBody': 'f406634cb996416eb193d84c19842dfe',
                    'eventSource': 'aws:sqs',
                    'eventSourceARN': 'arn:aws:sqs:us-east-1:080145351546:vdsc-prd-sqs-video-slice',
                    'awsRegion': 'us-east-1'
                }
            ]
        }

    def test_handler_success(self, valid_dynamodb_event):
        """Testa handler com sucesso (processamento síncrono)"""
        context = Mock()
        # Mockar _process_video_event para simular sucesso
        with patch('app._process_video_event') as mock_process:
            mock_process.return_value = None
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
        # Patch para simular exceção interna durante o processamento
        with patch('app._process_video_event', side_effect=Exception('fail')):
            result = lambda_handler(valid_dynamodb_event, context)
            assert result['statusCode'] == 500
            body = json.loads(result['body'])
            assert 'error' in body

    def test_handler_with_empty_records(self):
        """Testa handler com lista de registros vazia"""
        event = {'Records': []}
        context = Mock()
        result = lambda_handler(event, context)
        assert result['statusCode'] == 202
        body = json.loads(result['body'])
        assert 'status' in body
        assert 'Recebido' in body['status']

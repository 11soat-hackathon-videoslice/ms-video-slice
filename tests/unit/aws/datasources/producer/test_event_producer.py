"""Testes unitários para EventProducer"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from src.aws.datasources.producer.event_producer import EventProducer


@pytest.mark.unit
class TestEventProducer:
    """Testes para o produtor de eventos"""

    @pytest.fixture
    def event_producer(self):
        """Fixture para criar instância do EventProducer com mock de scheduler"""
        with patch('src.aws.datasources.producer.event_producer.boto3.client'):
            return EventProducer()

    def test_send_schedule_retry_event(self, event_producer):
        """Testa envio de evento de retry agendado com dados no formato DynamoDB"""
        metadata_dynamodb = {
            "videoId": {"S": "123"},
            "status": {"S": "processing"},
            "retries": {"N": "0"},
            "maxRetry": {"N": "3"}
        }
        schedule_time = datetime(2026, 1, 13, 0, 0, 0)
        schedule_config = {
            "retry_backoff_factor": 5,
            "retry_arn": "arn:aws:sqs:us-east-1:123456789012:queue",
            "retry_role_arn": "arn:aws:iam::123456789012:role/scheduler-role",
            "retry_dlq": "arn:aws:sqs:us-east-1:123456789012:dlq"
        }

        # Mock do scheduler cliente
        event_producer.scheduler = Mock()
        event_producer.scheduler.create_schedule = Mock()

        # Executar o método
        event_producer.send_schedule_retry_event(metadata_dynamodb, schedule_time, schedule_config)

        # Verificar que create_schedule foi chamado
        event_producer.scheduler.create_schedule.assert_called_once()
        call_args = event_producer.scheduler.create_schedule.call_args
        assert call_args[1]['Name'].startswith('vdsc-123-retry-0-of-3')
        assert call_args[1]['ScheduleExpression'] == 'at(2026-01-13T00:00:00)'

    def test_send_schedule_retry_event_with_retry_backoff(self, event_producer):
        """Testa envio de evento com retry backoff e múltiplas tentativas"""
        metadata_dynamodb = {
            "videoId": {"S": "456"},
            "retries": {"N": "2"},
            "maxRetry": {"N": "5"}
        }
        schedule_time = datetime(2026, 1, 14, 10, 30, 0)
        schedule_config = {
            "retry_backoff_factor": 10,
            "retry_arn": "arn:aws:sqs:us-east-1:123456789012:queue",
            "retry_role_arn": "arn:aws:iam::123456789012:role/scheduler-role",
            "retry_dlq": "arn:aws:sqs:us-east-1:123456789012:dlq"
        }

        # Mock do scheduler cliente
        event_producer.scheduler = Mock()
        event_producer.scheduler.create_schedule = Mock()

        # Executar o método
        event_producer.send_schedule_retry_event(metadata_dynamodb, schedule_time, schedule_config)

        # Verificar que create_schedule foi chamado
        event_producer.scheduler.create_schedule.assert_called_once()
        call_args = event_producer.scheduler.create_schedule.call_args
        assert 'vdsc-456-retry-2-of-5' in call_args[1]['Name']
        assert call_args[1]['Target']['Input'] is not None

    def test_send_schedule_retry_event_error_handling(self, event_producer):
        """Testa tratamento de erro ao criar agendamento"""
        metadata_dynamodb = {
            "videoId": {"S": "789"},
            "retries": {"N": "1"},
            "maxRetry": {"N": "3"}
        }
        schedule_time = datetime(2026, 1, 15, 12, 0, 0)
        schedule_config = {
            "retry_backoff_factor": 5,
            "retry_arn": "arn:aws:sqs:us-east-1:123456789012:queue",
            "retry_role_arn": "arn:aws:iam::123456789012:role/scheduler-role",
            "retry_dlq": "arn:aws:sqs:us-east-1:123456789012:dlq"
        }

        # Mock do scheduler cliente com erro
        event_producer.scheduler = Mock()
        event_producer.scheduler.create_schedule = Mock(side_effect=Exception("Scheduler error"))

        # Deve lançar exceção
        with pytest.raises(Exception, match="Scheduler error"):
            event_producer.send_schedule_retry_event(metadata_dynamodb, schedule_time, schedule_config)

    def test_send_notification(self, event_producer):
        """Testa envio de notificação (implementação vazia)"""
        metadata = {"videoId": "123"}
        channels = ["email", "sms"]
        message = "Vídeo processado"

        # A implementação é vazia, então apenas verifica que não gera erro
        result = event_producer.send_notification(metadata, channels, message)
        assert result is None



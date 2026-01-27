"""Testes unitários para EventProducer"""
import pytest
from src.aws.datasources.producer.event_producer import EventProducer


@pytest.mark.unit
class TestEventProducer:
    """Testes para o produtor de eventos"""

    @pytest.fixture
    def event_producer(self):
        """Fixture para criar instância do EventProducer"""
        return EventProducer()

    def test_send_event(self, event_producer):
        """Testa envio de evento (implementação vazia)"""
        event_data = {"event": "test", "video_id": "123"}
        # Como a implementação está vazia, apenas verificamos que não gera erro
        result = event_producer.send_event(event_data)
        assert result is None

    def test_send_event_with_none(self, event_producer):
        """Testa envio de evento com None"""
        result = event_producer.send_event(None)
        assert result is None

    def test_send_event_with_empty_dict(self, event_producer):
        """Testa envio de evento com dicionário vazio"""
        result = event_producer.send_event({})
        assert result is None

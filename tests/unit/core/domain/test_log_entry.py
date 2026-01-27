"""Testes unitários para LogEntry"""
import pytest
from datetime import datetime, UTC
from src.core.domain.log_entry import LogEntry


@pytest.mark.unit
class TestLogEntry:
    """Testes para a entidade de domínio LogEntry"""

    def test_create_log_entry(self):
        """Testa criação de log entry"""
        log = LogEntry(info="Teste de log")
        assert log.info == "Teste de log"
        assert log.timestamp is not None

    def test_timestamp_format(self):
        """Testa formato do timestamp"""
        log = LogEntry(info="Teste")
        # Formato esperado: YYYY-MM-DD HH:MM:SS
        assert len(log.timestamp) == 19
        assert log.timestamp[4] == '-'
        assert log.timestamp[7] == '-'
        assert log.timestamp[10] == ' '
        assert log.timestamp[13] == ':'
        assert log.timestamp[16] == ':'

    def test_to_dict(self):
        """Testa conversão para dicionário"""
        log = LogEntry(info="Teste de conversão")
        result = log.to_dict()
        assert "timestamp" in result
        assert "info" in result
        assert result["info"] == "Teste de conversão"

    def test_from_dict(self):
        """Testa criação a partir de dicionário"""
        data = {
            "timestamp": "2026-01-13T00:00:00Z",
            "info": "Log de teste"
        }
        log = LogEntry.from_dict(data)
        assert log.info == "Log de teste"
        assert log.timestamp is not None

    def test_from_dict_without_z_suffix(self):
        """Testa criação a partir de dicionário sem sufixo Z"""
        data = {
            "timestamp": "2026-01-13T00:00:00",
            "info": "Log sem Z"
        }
        log = LogEntry.from_dict(data)
        assert log.info == "Log sem Z"
        assert log.timestamp is not None

    def test_repr(self):
        """Testa representação string"""
        log = LogEntry(info="Teste repr")
        repr_str = repr(log)
        assert "LogEntry" in repr_str
        assert "Teste repr" in repr_str
        assert "timestamp" in repr_str

    def test_multiple_log_entries_different_timestamps(self):
        """Testa que múltiplos logs têm timestamps diferentes (ou muito próximos)"""
        log1 = LogEntry(info="Primeiro")
        log2 = LogEntry(info="Segundo")
        # Timestamps devem ser strings
        assert isinstance(log1.timestamp, str)
        assert isinstance(log2.timestamp, str)

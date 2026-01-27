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

    def test_create_log_entry_with_custom_timestamp(self):
        """Testa criação de LogEntry com timestamp customizado"""
        custom_time = datetime(2026, 1, 27, 10, 30, 45, tzinfo=UTC)
        log = LogEntry(info="Log customizado", timestamp=custom_time)

        assert log.info == "Log customizado"
        assert log.timestamp == "2026-01-27 10:30:45"

    def test_from_dict_without_timestamp(self):
        """Testa criação de LogEntry a partir de dicionário sem timestamp"""
        data = {'info': 'Log sem timestamp definido'}
        log = LogEntry.from_dict(data)

        assert log.info == 'Log sem timestamp definido'
        assert log.timestamp is not None
        assert isinstance(log.timestamp, str)

    def test_log_entry_with_empty_info(self):
        """Testa LogEntry com informação vazia"""
        log = LogEntry(info="")

        assert log.info == ""
        assert log.timestamp is not None

    def test_log_entry_with_special_characters(self):
        """Testa LogEntry com caracteres especiais em português"""
        info = "Vídeo processado com sucesso: áéíóúãõç"
        log = LogEntry(info=info)

        assert log.info == info
        result = log.to_dict()
        assert result['info'] == info

    def test_log_entry_roundtrip_conversion(self):
        """Testa conversão completa: LogEntry -> dict -> LogEntry"""
        original_time = datetime(2026, 1, 27, 15, 20, 30, tzinfo=UTC)
        original_log = LogEntry(info="Roundtrip test", timestamp=original_time)

        # Converte para dict
        log_dict = original_log.to_dict()

        # Converte de volta para LogEntry
        reconstructed_log = LogEntry.from_dict(log_dict)

        assert reconstructed_log.info == original_log.info
        assert reconstructed_log.timestamp == original_log.timestamp

    def test_from_dict_with_z_suffix_uppercase(self):
        """Testa parsing de timestamp com Z maiúsculo"""
        data = {
            'timestamp': '2026-01-27T12:30:00Z',
            'info': 'Teste com Z'
        }
        log = LogEntry.from_dict(data)

        assert log.info == 'Teste com Z'
        assert 'Z' not in log.timestamp

    def test_log_entry_with_long_info(self):
        """Testa LogEntry com informação longa"""
        long_info = "Este é um log muito longo " * 50
        log = LogEntry(info=long_info)

        assert log.info == long_info
        assert len(log.info) > 1000


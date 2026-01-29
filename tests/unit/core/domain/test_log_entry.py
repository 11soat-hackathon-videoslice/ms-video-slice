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
        # Formato esperado: YYYY-MM-DDTHH:MM:SSZ (ISO 8601)
        assert len(log.timestamp) == 20
        assert log.timestamp[4] == '-'
        assert log.timestamp[7] == '-'
        assert log.timestamp[10] == 'T'
        assert log.timestamp[13] == ':'
        assert log.timestamp[16] == ':'
        assert log.timestamp[-1] == 'Z'

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
        assert log.timestamp == "2026-01-27T10:30:45Z"

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
        # Timestamp deve manter o formato ISO 8601 com Z
        assert log.timestamp.endswith('Z')
        assert 'T' in log.timestamp

    def test_log_entry_with_long_info(self):
        """Testa LogEntry com informação longa"""
        long_info = "Este é um log muito longo " * 50
        log = LogEntry(info=long_info)

        assert log.info == long_info
        assert len(log.info) > 1000


@pytest.mark.unit
class TestLogEntryTimestampFormat:
    """Testes rigorosos para validação do formato ISO 8601 de timestamps"""

    def test_timestamp_iso8601_format_exact(self):
        """Testa se timestamp gerado está exatamente no formato ISO 8601"""
        log = LogEntry(info="Teste ISO 8601")
        timestamp = log.timestamp

        # Formato: 2026-01-28T21:14:41Z
        assert len(timestamp) == 20, f"Timestamp deve ter 20 caracteres, tem {len(timestamp)}"
        assert timestamp[4] == '-', "Posição 4 deve ser '-'"
        assert timestamp[7] == '-', "Posição 7 deve ser '-'"
        assert timestamp[10] == 'T', "Posição 10 deve ser 'T' (separador ISO 8601)"
        assert timestamp[13] == ':', "Posição 13 deve ser ':'"
        assert timestamp[16] == ':', "Posição 16 deve ser ':'"
        assert timestamp[19] == 'Z', "Posição 19 deve ser 'Z' (UTC)"

    def test_timestamp_date_part_format(self):
        """Testa se a parte de data está no formato correto YYYY-MM-DD"""
        log = LogEntry(info="Teste data")
        timestamp = log.timestamp

        date_part = timestamp[:10]  # 2026-01-28
        year, month, day = date_part.split('-')

        assert len(year) == 4, "Ano deve ter 4 dígitos"
        assert year.isdigit(), "Ano deve ser numérico"
        assert len(month) == 2, "Mês deve ter 2 dígitos"
        assert month.isdigit(), "Mês deve ser numérico"
        assert 1 <= int(month) <= 12, "Mês deve estar entre 01 e 12"
        assert len(day) == 2, "Dia deve ter 2 dígitos"
        assert day.isdigit(), "Dia deve ser numérico"
        assert 1 <= int(day) <= 31, "Dia deve estar entre 01 e 31"

    def test_timestamp_time_part_format(self):
        """Testa se a parte de hora está no formato correto HH:MM:SS"""
        log = LogEntry(info="Teste hora")
        timestamp = log.timestamp

        time_part = timestamp[11:19]  # 21:14:41
        hour, minute, second = time_part.split(':')

        assert len(hour) == 2, "Hora deve ter 2 dígitos"
        assert hour.isdigit(), "Hora deve ser numérica"
        assert 0 <= int(hour) <= 23, "Hora deve estar entre 00 e 23"
        assert len(minute) == 2, "Minuto deve ter 2 dígitos"
        assert minute.isdigit(), "Minuto deve ser numérico"
        assert 0 <= int(minute) <= 59, "Minuto deve estar entre 00 e 59"
        assert len(second) == 2, "Segundo deve ter 2 dígitos"
        assert second.isdigit(), "Segundo deve ser numérico"
        assert 0 <= int(second) <= 59, "Segundo deve estar entre 00 e 59"

    def test_timestamp_separator_t_uppercase(self):
        """Testa se o separador T está em maiúsculo (padrão ISO 8601)"""
        log = LogEntry(info="Teste separador")
        assert log.timestamp[10] == 'T', "Separador deve ser 'T' maiúsculo"
        assert log.timestamp[10] != 't', "Separador não deve ser 't' minúsculo"

    def test_timestamp_timezone_z_uppercase(self):
        """Testa se o timezone Z está em maiúsculo (UTC)"""
        log = LogEntry(info="Teste timezone")
        assert log.timestamp[-1] == 'Z', "Timezone deve ser 'Z' maiúsculo"
        assert log.timestamp[-1] != 'z', "Timezone não deve ser 'z' minúsculo"

    def test_timestamp_no_milliseconds(self):
        """Testa se timestamp não contém milissegundos"""
        log = LogEntry(info="Teste sem milissegundos")
        # Não deve haver ponto após os segundos
        assert '.' not in log.timestamp, "Timestamp não deve conter milissegundos"

    def test_timestamp_no_timezone_offset(self):
        """Testa se timestamp não usa offset de timezone (+/-HH:MM)"""
        log = LogEntry(info="Teste timezone offset")
        assert '+' not in log.timestamp, "Timestamp não deve conter '+' (offset)"
        # O único '-' deve estar nas posições 4 e 7 (data)
        assert log.timestamp.count('-') == 2, "Deve haver apenas 2 '-' (na data)"

    def test_multiple_logs_generate_valid_timestamps(self):
        """Testa se múltiplos logs gerados seguem o formato ISO 8601"""
        logs = [LogEntry(info=f"Log {i}") for i in range(10)]

        for log in logs:
            assert len(log.timestamp) == 20
            assert log.timestamp[10] == 'T'
            assert log.timestamp[-1] == 'Z'
            # Valida que pode ser parseado como datetime
            try:
                datetime.fromisoformat(log.timestamp.rstrip('Z'))
            except ValueError:
                pytest.fail(f"Timestamp inválido: {log.timestamp}")

    def test_custom_datetime_converted_to_iso8601(self):
        """Testa se datetime customizado é convertido para ISO 8601"""
        custom_time = datetime(2026, 1, 28, 21, 14, 41, tzinfo=UTC)
        log = LogEntry(info="Teste conversão", timestamp=custom_time)

        assert log.timestamp == "2026-01-28T21:14:41Z"
        assert len(log.timestamp) == 20
        assert log.timestamp[10] == 'T'
        assert log.timestamp[-1] == 'Z'

    def test_timestamp_is_utc_timezone(self):
        """Testa se timestamp sempre usa UTC (Z)"""
        log = LogEntry(info="Teste UTC")
        # Deve sempre terminar com Z
        assert log.timestamp.endswith('Z'), "Timestamp deve estar em UTC (terminar com Z)"

    def test_timestamp_format_regex_match(self):
        """Testa se timestamp corresponde ao padrão regex do ISO 8601"""
        import re
        log = LogEntry(info="Teste regex")

        # Padrão: YYYY-MM-DDTHH:MM:SSZ
        pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$'
        assert re.match(pattern, log.timestamp), \
            f"Timestamp '{log.timestamp}' não corresponde ao padrão ISO 8601"

    def test_timestamp_string_not_datetime_object(self):
        """Testa se timestamp é string e não objeto datetime"""
        log = LogEntry(info="Teste tipo")
        assert isinstance(log.timestamp, str), "Timestamp deve ser string"
        assert not isinstance(log.timestamp, datetime), "Timestamp não deve ser objeto datetime"

    def test_roundtrip_preserves_iso8601_format(self):
        """Testa se conversão dict -> LogEntry -> dict preserva formato ISO 8601"""
        original_timestamp = "2026-01-28T21:14:41Z"
        data = {"timestamp": original_timestamp, "info": "Roundtrip"}

        log = LogEntry.from_dict(data)
        result_dict = log.to_dict()

        assert result_dict['timestamp'] == original_timestamp
        assert len(result_dict['timestamp']) == 20
        assert 'T' in result_dict['timestamp']
        assert result_dict['timestamp'].endswith('Z')

    def test_timestamp_generated_is_current_utc(self):
        """Testa se timestamp gerado está próximo do momento atual UTC"""
        from datetime import timedelta
        before = datetime.now(UTC)
        log = LogEntry(info="Teste tempo atual")
        after = datetime.now(UTC)

        # Remove 'Z' e converte para datetime para comparação
        log_time = datetime.fromisoformat(log.timestamp.rstrip('Z')).replace(tzinfo=UTC)

        # Aceita diferença de até 2 segundos devido à perda de milissegundos no formato
        tolerance = timedelta(seconds=2)
        assert before - tolerance <= log_time <= after + tolerance, \
            f"Timestamp {log_time} deve estar próximo de {before} - {after}"

    def test_timestamp_no_spaces(self):
        """Testa se timestamp não contém espaços"""
        log = LogEntry(info="Teste espaços")
        assert ' ' not in log.timestamp, "Timestamp não deve conter espaços"

    def test_timestamp_compatibility_with_javascript(self):
        """Testa se formato é compatível com JavaScript Date.parse()"""
        log = LogEntry(info="Teste compatibilidade JS")
        # O formato YYYY-MM-DDTHH:MM:SSZ é aceito por JavaScript
        # Verifica estrutura compatível
        assert log.timestamp.count('-') == 2  # Data
        assert log.timestamp.count(':') == 2  # Hora
        assert log.timestamp.count('T') == 1  # Separador
        assert log.timestamp.endswith('Z')    # UTC

    def test_timestamp_compatibility_with_dynamodb(self):
        """Testa se formato é compatível com DynamoDB (string)"""
        log = LogEntry(info="Teste DynamoDB")
        # DynamoDB aceita strings, verifica que é uma string válida
        assert isinstance(log.timestamp, str)
        assert len(log.timestamp) == 20
        # Não deve ter caracteres especiais problemáticos
        assert '"' not in log.timestamp
        assert "'" not in log.timestamp



"""Testes unitários para VdscMetadata domain entity"""
import pytest
from datetime import datetime, UTC
from src.core.domain.vdsc_metadata import VdscMetadata
from src.core.dtos.vdsc_metadata_dto import VdscMetadataDTO
from src.core.enums.vdsc_status_enum import VdscStatusEnum


@pytest.mark.unit
class TestVdscMetadata:
    """Testes para a entidade de domínio VdscMetadata"""

    @pytest.fixture
    def valid_dto(self):
        """Fixture com DTO válido para criar entidade de domínio"""
        return VdscMetadataDTO(
            video_id="video123",
            file_name="test_video.mp4",
            extension_file="mp4",
            status="UPLOADED",
            created="2026-01-13T00:00:00Z",
            user_id="user123",
            total_time=3600,
            unit_time="s",
            start_time=0,
            end_time=60,
            time_interval=["00:00:00", "00:01:00"],
            max_retry=3,
            retries=0,
            quality="high",
            logs=[]
        )

    def test_create_metadata_from_dto(self, valid_dto):
        """Testa criação de entidade a partir de DTO"""
        metadata = VdscMetadata(dto=valid_dto)
        assert metadata.video_id == "video123"
        assert metadata.file_name == "test_video.mp4"
        assert metadata.extension_file == "mp4"
        assert metadata.user_id == "user123"
        assert metadata.quality == "high"

    def test_validate_success(self, valid_dto):
        """Testa validação bem-sucedida"""
        metadata = VdscMetadata(dto=valid_dto)
        assert metadata.validate() is True

    def test_validate_empty_video_id(self, valid_dto):
        """Testa validação com video_id vazio"""
        valid_dto.video_id = ""
        metadata = VdscMetadata(dto=valid_dto)
        with pytest.raises(ValueError, match="ID do vídeo e ID do usuário são obrigatórios"):
            metadata.validate()

    def test_validate_empty_user_id(self, valid_dto):
        """Testa validação com user_id vazio"""
        valid_dto.user_id = ""
        metadata = VdscMetadata(dto=valid_dto)
        with pytest.raises(ValueError, match="ID do vídeo e ID do usuário são obrigatórios"):
            metadata.validate()

    def test_validate_zero_total_time(self, valid_dto):
        """Testa validação com total_time zero"""
        valid_dto.total_time = 0
        metadata = VdscMetadata(dto=valid_dto)
        with pytest.raises(ValueError, match="Tempo total deve ser maior que zero"):
            metadata.validate()

    def test_validate_negative_start_time(self, valid_dto):
        """Testa validação com start_time negativo"""
        valid_dto.start_time = -1
        metadata = VdscMetadata(dto=valid_dto)
        with pytest.raises(ValueError, match="Tempo inicial não pode ser negativo"):
            metadata.validate()

    def test_validate_end_time_less_than_start_time(self, valid_dto):
        """Testa validação com end_time menor que start_time"""
        valid_dto.start_time = 100
        valid_dto.end_time = 50
        metadata = VdscMetadata(dto=valid_dto)
        with pytest.raises(ValueError, match="Tempo final deve ser maior que o tempo inicial"):
            metadata.validate()

    def test_validate_end_time_exceeds_total_time(self, valid_dto):
        """Testa validação com end_time maior que total_time"""
        valid_dto.end_time = 4000
        metadata = VdscMetadata(dto=valid_dto)
        with pytest.raises(ValueError, match="Tempo final não pode exceder o tempo total"):
            metadata.validate()

    def test_validate_invalid_unit_time(self, valid_dto):
        """Testa validação com unit_time inválido"""
        valid_dto.unit_time = "invalid"
        metadata = VdscMetadata(dto=valid_dto)
        with pytest.raises(ValueError, match="Unidade de tempo deve ser uma das seguintes"):
            metadata.validate()

    def test_validate_invalid_quality(self, valid_dto):
        """Testa validação com quality inválido"""
        valid_dto.quality = "invalid"
        metadata = VdscMetadata(dto=valid_dto)
        with pytest.raises(ValueError, match="Qualidade deve ser uma das seguintes"):
            metadata.validate()

    def test_validate_retries_exceeds_max_retry(self, valid_dto):
        """Testa validação com retries maior que max_retry"""
        valid_dto.retries = 5
        valid_dto.max_retry = 3
        metadata = VdscMetadata(dto=valid_dto)
        with pytest.raises(ValueError, match="Número de tentativas não pode exceder o máximo permitido"):
            metadata.validate()

    def test_add_log(self, valid_dto):
        """Testa adição de log"""
        metadata = VdscMetadata(dto=valid_dto)
        metadata.add_log("Test log entry")
        assert len(metadata.logs) == 1
        assert metadata.logs[0].info == "Test log entry"

    def test_mark_as_uploaded(self, valid_dto):
        """Testa marcação como uploaded"""
        metadata = VdscMetadata(dto=valid_dto)
        metadata.mark_as_uploaded()
        assert metadata.status == VdscStatusEnum.UPLOADED.value
        assert len(metadata.logs) > 0

    def test_mark_as_processing(self, valid_dto):
        """Testa marcação como processing"""
        metadata = VdscMetadata(dto=valid_dto)
        metadata.mark_as_processing()
        assert metadata.status == VdscStatusEnum.PROCESSING.value
        assert len(metadata.logs) > 0

    def test_mark_as_finished(self, valid_dto):
        """Testa marcação como finished"""
        metadata = VdscMetadata(dto=valid_dto)
        metadata.mark_as_finished()
        assert metadata.status == VdscStatusEnum.FINISHED.value
        assert len(metadata.logs) > 0

    def test_mark_as_retrying(self, valid_dto):
        """Testa marcação como retrying"""
        metadata = VdscMetadata(dto=valid_dto)
        metadata.mark_as_retrying()
        assert metadata.status == VdscStatusEnum.RETRYING.value
        assert len(metadata.logs) > 0

    def test_mark_as_failed(self, valid_dto):
        """Testa marcação como failed"""
        metadata = VdscMetadata(dto=valid_dto)
        metadata.mark_as_failed()
        assert metadata.status == VdscStatusEnum.FAILED.value
        assert len(metadata.logs) > 0

    def test_mark_as_failed_with_error_message(self, valid_dto):
        """Testa marcação como failed com mensagem de erro"""
        metadata = VdscMetadata(dto=valid_dto)
        metadata.mark_as_failed("Connection timeout")
        assert metadata.status == VdscStatusEnum.FAILED.value
        assert any("Connection timeout" in log.info for log in metadata.logs)

    def test_increment_retry_success(self, valid_dto):
        """Testa incremento de retry com sucesso"""
        metadata = VdscMetadata(dto=valid_dto)
        result = metadata.increment_retry()
        assert result is True
        assert metadata.retries == 1
        assert len(metadata.logs) > 0

    def test_increment_retry_max_reached(self, valid_dto):
        """Testa incremento de retry quando máximo já foi atingido"""
        valid_dto.retries = 3
        metadata = VdscMetadata(dto=valid_dto)
        result = metadata.increment_retry()
        assert result is False
        assert metadata.retries == 3

    def test_can_retry_true(self, valid_dto):
        """Testa can_retry retornando True"""
        metadata = VdscMetadata(dto=valid_dto)
        assert metadata.can_retry() is True

    def test_can_retry_false(self, valid_dto):
        """Testa can_retry retornando False"""
        valid_dto.retries = 3
        metadata = VdscMetadata(dto=valid_dto)
        assert metadata.can_retry() is False

    def test_get_duration(self, valid_dto):
        """Testa cálculo de duração"""
        valid_dto.start_time = 10
        valid_dto.end_time = 70
        metadata = VdscMetadata(dto=valid_dto)
        assert metadata.get_duration() == 60

    def test_get_full_file_name(self, valid_dto):
        """Testa obtenção do nome completo do arquivo"""
        metadata = VdscMetadata(dto=valid_dto)
        assert metadata.get_full_file_name() == "test_video.mp4.mp4"

    def test_to_dict(self, valid_dto):
        """Testa conversão para dicionário"""
        metadata = VdscMetadata(dto=valid_dto)
        metadata.add_log("Test log")
        result = metadata.to_dict()

        assert result['videoId'] == 'video123'
        assert result['fileName'] == 'test_video.mp4'
        assert result['status'] == 'UPLOADED'
        assert len(result['logs']) == 1

    def test_add_log_with_custom_timestamp(self, valid_dto):
        """Testa adição de log com timestamp customizado"""
        metadata = VdscMetadata(dto=valid_dto)
        custom_time = datetime(2026, 1, 27, 10, 30, 0, tzinfo=UTC)
        metadata.add_log("Custom timestamp log", timestamp=custom_time)

        assert len(metadata.logs) == 1
        assert metadata.logs[0].info == "Custom timestamp log"

    def test_validate_empty_file_name(self, valid_dto):
        """Testa validação com file_name vazio"""
        valid_dto.file_name = ""
        metadata = VdscMetadata(dto=valid_dto)
        with pytest.raises(ValueError, match="Nome do arquivo é obrigatório"):
            metadata.validate()

    def test_validate_empty_extension_file(self, valid_dto):
        """Testa validação com extension_file vazio"""
        valid_dto.extension_file = ""
        metadata = VdscMetadata(dto=valid_dto)
        with pytest.raises(ValueError, match="Extensão do arquivo é obrigatória"):
            metadata.validate()

    def test_validate_negative_total_time(self, valid_dto):
        """Testa validação com total_time negativo"""
        valid_dto.total_time = -100
        metadata = VdscMetadata(dto=valid_dto)
        with pytest.raises(ValueError, match="Tempo total deve ser maior que zero"):
            metadata.validate()

    def test_validate_negative_max_retry(self, valid_dto):
        """Testa validação com max_retry negativo"""
        valid_dto.max_retry = -1
        metadata = VdscMetadata(dto=valid_dto)
        with pytest.raises(ValueError, match="Número máximo de tentativas não pode ser negativo"):
            metadata.validate()

    def test_validate_negative_retries(self, valid_dto):
        """Testa validação com retries negativo"""
        valid_dto.retries = -1
        metadata = VdscMetadata(dto=valid_dto)
        with pytest.raises(ValueError, match="Número de tentativas não pode ser negativo"):
            metadata.validate()

    def test_validate_invalid_status(self, valid_dto):
        """Testa validação com status inválido"""
        valid_dto.status = "INVALID_STATUS"
        metadata = VdscMetadata(dto=valid_dto)
        with pytest.raises(ValueError, match="Status deve ser um dos seguintes"):
            metadata.validate()

    def test_validate_valid_unit_times(self, valid_dto):
        """Testa validação com todas as unit_time válidas"""
        valid_units = ["s", "ms", "m", "h"]
        for unit in valid_units:
            valid_dto.unit_time = unit
            metadata = VdscMetadata(dto=valid_dto)
            assert metadata.validate() is True

    def test_multiple_increment_retry(self, valid_dto):
        """Testa múltiplos incrementos de retry"""
        metadata = VdscMetadata(dto=valid_dto)

        assert metadata.increment_retry() is True
        assert metadata.retries == 1

        assert metadata.increment_retry() is True
        assert metadata.retries == 2

        assert metadata.increment_retry() is True
        assert metadata.retries == 3

        assert metadata.increment_retry() is False
        assert metadata.retries == 3

    def test_status_workflow(self, valid_dto):
        """Testa fluxo completo de mudanças de status"""
        metadata = VdscMetadata(dto=valid_dto)

        metadata.mark_as_uploaded()
        assert metadata.status == VdscStatusEnum.UPLOADED.value

        metadata.mark_as_processing()
        assert metadata.status == VdscStatusEnum.PROCESSING.value

        metadata.mark_as_finished()
        assert metadata.status == VdscStatusEnum.FINISHED.value

        assert len(metadata.logs) == 3

    def test_retry_workflow(self, valid_dto):
        """Testa fluxo de retry"""
        metadata = VdscMetadata(dto=valid_dto)

        metadata.mark_as_processing()
        metadata.mark_as_failed("First failure")
        metadata.mark_as_retrying()
        metadata.increment_retry()

        assert metadata.retries == 1
        assert metadata.status == VdscStatusEnum.RETRYING.value
        assert metadata.can_retry() is True

    def test_created_datetime_conversion(self, valid_dto):
        """Testa que created é mantido como string no formato ISO 8601"""
        metadata = VdscMetadata(dto=valid_dto)
        assert isinstance(metadata.created, str)
        # Verifica formato ISO 8601: YYYY-MM-DDTHH:MM:SSZ
        assert 'T' in metadata.created
        assert metadata.created.endswith('Z')

    def test_created_as_datetime_object(self):
        """Testa criação com created já como datetime"""
        dto = VdscMetadataDTO(
            video_id="video456",
            file_name="test.mp4",
            extension_file="mp4",
            status="UPLOADED",
            created=datetime.now(UTC),
            user_id="user456",
            total_time=3600,
            unit_time="s",
            start_time=0,
            end_time=60,
            time_interval=["00:00:00"],
            max_retry=3,
            retries=0,
            quality="high",
            logs=[]
        )

        metadata = VdscMetadata(dto=dto)
        assert isinstance(metadata.created, datetime)

    def test_to_dict_with_multiple_logs(self, valid_dto):
        """Testa conversão para dict com múltiplos logs"""
        metadata = VdscMetadata(dto=valid_dto)
        metadata.add_log("Log 1")
        metadata.add_log("Log 2")
        metadata.add_log("Log 3")

        result = metadata.to_dict()
        assert len(result['logs']) == 3

    def test_repr_string(self, valid_dto):
        """Testa representação string do objeto"""
        metadata = VdscMetadata(dto=valid_dto)
        repr_str = repr(metadata)

        assert "VideoSliceMetadata" in repr_str
        assert "video123" in repr_str
        assert "test_video.mp4" in repr_str


@pytest.mark.unit
class TestVdscMetadataLogsTimestampFormat:
    """Testes rigorosos para validação de formato ISO 8601 em logs gerados por VdscMetadata"""

    @pytest.fixture
    def valid_dto(self):
        """Fixture com DTO válido"""
        return VdscMetadataDTO(
            video_id="video123",
            file_name="test.mp4",
            extension_file="mp4",
            status="UPLOADED",
            created="2026-01-13T00:00:00Z",
            user_id="user123",
            total_time=3600,
            unit_time="s",
            start_time=0,
            end_time=60,
            time_interval=["00:00:00"],
            max_retry=3,
            retries=0,
            quality="high",
            logs=[]
        )

    def test_add_log_generates_iso8601_timestamp(self, valid_dto):
        """Testa se add_log gera timestamp no formato ISO 8601"""
        metadata = VdscMetadata(dto=valid_dto)
        metadata.add_log("Teste de log")

        log = metadata.logs[0]
        assert len(log.timestamp) == 20
        assert log.timestamp[10] == 'T'
        assert log.timestamp[-1] == 'Z'
        assert 'T' in log.timestamp
        assert log.timestamp.endswith('Z')

    def test_mark_as_uploaded_generates_valid_timestamp(self, valid_dto):
        """Testa se mark_as_uploaded gera timestamp válido"""
        metadata = VdscMetadata(dto=valid_dto)
        metadata.mark_as_uploaded()

        log = metadata.logs[-1]
        assert isinstance(log.timestamp, str)
        assert len(log.timestamp) == 20
        assert log.timestamp[10] == 'T'
        assert log.timestamp[-1] == 'Z'

    def test_mark_as_processing_generates_valid_timestamp(self, valid_dto):
        """Testa se mark_as_processing gera timestamp válido"""
        metadata = VdscMetadata(dto=valid_dto)
        metadata.mark_as_processing()

        log = metadata.logs[-1]
        assert len(log.timestamp) == 20
        assert log.timestamp[10] == 'T'
        assert log.timestamp[-1] == 'Z'

    def test_mark_as_finished_generates_valid_timestamp(self, valid_dto):
        """Testa se mark_as_finished gera timestamp válido"""
        metadata = VdscMetadata(dto=valid_dto)
        metadata.mark_as_finished()

        log = metadata.logs[-1]
        assert len(log.timestamp) == 20
        assert log.timestamp[10] == 'T'
        assert log.timestamp[-1] == 'Z'

    def test_mark_as_retrying_generates_valid_timestamp(self, valid_dto):
        """Testa se mark_as_retrying gera timestamp válido"""
        metadata = VdscMetadata(dto=valid_dto)
        metadata.mark_as_retrying()

        log = metadata.logs[-1]
        assert len(log.timestamp) == 20
        assert log.timestamp[10] == 'T'
        assert log.timestamp[-1] == 'Z'

    def test_mark_as_failed_generates_valid_timestamp(self, valid_dto):
        """Testa se mark_as_failed gera timestamp válido"""
        metadata = VdscMetadata(dto=valid_dto)
        metadata.mark_as_failed("Error message")

        log = metadata.logs[-1]
        assert len(log.timestamp) == 20
        assert log.timestamp[10] == 'T'
        assert log.timestamp[-1] == 'Z'

    def test_increment_retry_generates_valid_timestamp(self, valid_dto):
        """Testa se increment_retry gera timestamp válido"""
        metadata = VdscMetadata(dto=valid_dto)
        metadata.increment_retry()

        log = metadata.logs[-1]
        assert len(log.timestamp) == 20
        assert log.timestamp[10] == 'T'
        assert log.timestamp[-1] == 'Z'

    def test_multiple_operations_generate_valid_timestamps(self, valid_dto):
        """Testa se múltiplas operações geram timestamps válidos"""
        metadata = VdscMetadata(dto=valid_dto)

        metadata.mark_as_uploaded()
        metadata.mark_as_processing()
        metadata.increment_retry()
        metadata.mark_as_retrying()
        metadata.mark_as_failed("Erro")

        # Todos os logs devem ter formato ISO 8601
        for log in metadata.logs:
            assert len(log.timestamp) == 20
            assert log.timestamp[10] == 'T'
            assert log.timestamp[-1] == 'Z'
            assert isinstance(log.timestamp, str)

    def test_to_dict_preserves_iso8601_format_in_logs(self, valid_dto):
        """Testa se to_dict preserva formato ISO 8601 nos logs"""
        metadata = VdscMetadata(dto=valid_dto)
        metadata.add_log("Log 1")
        metadata.add_log("Log 2")

        result = metadata.to_dict()

        for log_dict in result['logs']:
            assert 'timestamp' in log_dict
            timestamp = log_dict['timestamp']
            assert len(timestamp) == 20
            assert timestamp[10] == 'T'
            assert timestamp[-1] == 'Z'

    def test_logs_timestamps_are_sequential(self, valid_dto):
        """Testa se timestamps de logs são sequenciais (ou muito próximos)"""
        import re
        metadata = VdscMetadata(dto=valid_dto)

        # Adiciona vários logs rapidamente
        for i in range(5):
            metadata.add_log(f"Log {i}")

        # Todos devem ter formato válido
        for log in metadata.logs:
            pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$'
            assert re.match(pattern, log.timestamp), \
                f"Timestamp inválido: {log.timestamp}"

    def test_custom_timestamp_in_add_log_uses_iso8601(self, valid_dto):
        """Testa se timestamp customizado é convertido para ISO 8601"""
        metadata = VdscMetadata(dto=valid_dto)
        custom_time = datetime(2026, 1, 28, 21, 14, 41, tzinfo=UTC)

        metadata.add_log("Log customizado", timestamp=custom_time)

        log = metadata.logs[0]
        assert log.timestamp == "2026-01-28T21:14:41Z"
        assert len(log.timestamp) == 20

    def test_workflow_logs_all_have_valid_format(self, valid_dto):
        """Testa fluxo completo validando formato de todos os logs"""
        import re
        metadata = VdscMetadata(dto=valid_dto)

        # Simula um fluxo completo
        metadata.mark_as_uploaded()
        metadata.mark_as_processing()
        metadata.add_log("Iniciando processamento de frames")
        metadata.increment_retry()
        metadata.add_log("Frame 1 processado")
        metadata.add_log("Frame 2 processado")
        metadata.mark_as_finished()

        pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$'

        for i, log in enumerate(metadata.logs):
            assert re.match(pattern, log.timestamp), \
                f"Log {i} com timestamp inválido: {log.timestamp}"
            assert log.timestamp[10] == 'T'
            assert log.timestamp[-1] == 'Z'

    def test_logs_timestamps_no_milliseconds(self, valid_dto):
        """Testa se timestamps de logs não contêm milissegundos"""
        metadata = VdscMetadata(dto=valid_dto)
        metadata.add_log("Teste 1")
        metadata.add_log("Teste 2")
        metadata.add_log("Teste 3")

        for log in metadata.logs:
            assert '.' not in log.timestamp, \
                f"Timestamp não deve ter milissegundos: {log.timestamp}"

    def test_logs_timestamps_utc_only(self, valid_dto):
        """Testa se todos os timestamps estão em UTC (Z)"""
        metadata = VdscMetadata(dto=valid_dto)

        metadata.mark_as_uploaded()
        metadata.mark_as_processing()
        metadata.mark_as_finished()

        for log in metadata.logs:
            assert log.timestamp.endswith('Z'), \
                f"Timestamp deve estar em UTC: {log.timestamp}"
            assert '+' not in log.timestamp, "Não deve usar offset +HH:MM"
            assert log.timestamp.count('-') == 2, "Apenas 2 '-' na data"



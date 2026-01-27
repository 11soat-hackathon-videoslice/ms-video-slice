"""Testes unitários para VdscMetadata domain entity"""
import pytest
from datetime import datetime, UTC
from src.core.domain.vdsc_metadata import VdscMetadata
from src.core.domain.log_entry import LogEntry
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

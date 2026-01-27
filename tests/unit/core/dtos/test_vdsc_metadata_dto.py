"""Testes unitários para VdscMetadataDTO"""
import pytest
from src.core.dtos.vdsc_metadata_dto import VdscMetadataDTO, LogEntryDTO


@pytest.mark.unit
class TestLogEntryDTO:
    """Testes para LogEntryDTO"""

    def test_valid_log_entry(self):
        """Testa criação de log entry válido"""
        log = LogEntryDTO(timestamp="2026-01-13T00:00:00Z", info="Teste log")
        assert log.timestamp == "2026-01-13T00:00:00Z"
        assert log.info == "Teste log"

    def test_validate_success(self):
        """Testa validação bem-sucedida"""
        log = LogEntryDTO(timestamp="2026-01-13T00:00:00Z", info="Teste")
        assert log.validate() is True

    def test_validate_empty_timestamp(self):
        """Testa validação com timestamp vazio"""
        log = LogEntryDTO(timestamp="", info="Teste")
        with pytest.raises(Exception):
            log.validate()

    def test_validate_empty_info(self):
        """Testa validação com info vazio"""
        log = LogEntryDTO(timestamp="2026-01-13T00:00:00Z", info="")
        with pytest.raises(Exception):
            log.validate()

    def test_to_dict(self):
        """Testa conversão para dicionário"""
        log = LogEntryDTO(timestamp="2026-01-13T00:00:00Z", info="Teste log")
        result = log.to_dict()
        assert result["timestamp"] == "2026-01-13T00:00:00Z"
        assert result["info"] == "Teste log"


@pytest.mark.unit
class TestVdscMetadataDTO:
    """Testes para VdscMetadataDTO"""

    @pytest.fixture
    def valid_metadata_dto(self):
        """Fixture com DTO válido"""
        return VdscMetadataDTO(
            video_id="video123",
            file_name="test_video.mp4",
            extension_file="mp4",
            status="uploaded",
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

    def test_create_valid_dto(self, valid_metadata_dto):
        """Testa criação de DTO válido"""
        assert valid_metadata_dto.video_id == "video123"
        assert valid_metadata_dto.file_name == "test_video.mp4"
        assert valid_metadata_dto.extension_file == "mp4"

    def test_validate_success(self, valid_metadata_dto):
        """Testa validação bem-sucedida"""
        assert valid_metadata_dto.validate() is True

    def test_validate_empty_video_id(self, valid_metadata_dto):
        """Testa validação com video_id vazio"""
        valid_metadata_dto.video_id = ""
        with pytest.raises(Exception):
            valid_metadata_dto.validate()

    def test_validate_empty_file_name(self, valid_metadata_dto):
        """Testa validação com file_name vazio"""
        valid_metadata_dto.file_name = ""
        with pytest.raises(Exception):
            valid_metadata_dto.validate()

    def test_validate_negative_total_time(self, valid_metadata_dto):
        """Testa validação com total_time negativo"""
        valid_metadata_dto.total_time = -1
        with pytest.raises(Exception):
            valid_metadata_dto.validate()

    def test_validate_start_time_greater_than_end_time(self, valid_metadata_dto):
        """Testa validação com start_time maior que end_time"""
        valid_metadata_dto.start_time = 100
        valid_metadata_dto.end_time = 50
        with pytest.raises(Exception):
            valid_metadata_dto.validate()

    def test_validate_empty_time_interval(self, valid_metadata_dto):
        """Testa validação com time_interval vazio"""
        valid_metadata_dto.time_interval = []
        with pytest.raises(Exception):
            valid_metadata_dto.validate()

    def test_validate_negative_retries(self, valid_metadata_dto):
        """Testa validação com retries negativo"""
        valid_metadata_dto.retries = -1
        with pytest.raises(Exception):
            valid_metadata_dto.validate()

    def test_validate_invalid_logs(self, valid_metadata_dto):
        """Testa validação com logs inválidos"""
        valid_metadata_dto.logs = ["invalid_log"]
        with pytest.raises(Exception):
            valid_metadata_dto.validate()

    def test_to_dict(self, valid_metadata_dto):
        """Testa conversão para dicionário"""
        result = valid_metadata_dto.to_dict()
        assert result["videoId"] == "video123"
        assert result["fileName"] == "test_video.mp4"
        assert result["status"] == "uploaded"

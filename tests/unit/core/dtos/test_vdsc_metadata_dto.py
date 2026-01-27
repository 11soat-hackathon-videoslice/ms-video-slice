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

    def test_from_dict(self):
        """Testa criação de DTO a partir de dicionário"""
        data = {
            'videoId': 'video456',
            'fileName': 'from_dict.mp4',
            'extension_file': 'mp4',
            'status': 'processing',
            'created': '2026-01-27T10:00:00Z',
            'userId': 'user456',
            'totalTime': 7200,
            'unitTime': 's',
            'startTime': 0,
            'endTime': 120,
            'timeInterval': ['00:00:00', '00:02:00'],
            'maxRetry': 5,
            'retries': 1,
            'quality': 'ultra',
            'logs': [{'timestamp': '2026-01-27T10:00:00Z', 'info': 'Processing started'}]
        }

        dto = VdscMetadataDTO.from_dict(data)

        assert dto.video_id == 'video456'
        assert dto.file_name == 'from_dict.mp4'
        assert dto.status == 'processing'
        assert len(dto.logs) == 1

    def test_to_dynamodb_item(self, valid_metadata_dto):
        """Testa conversão para item do DynamoDB"""
        log = LogEntryDTO(timestamp="2026-01-27T12:00:00Z", info="Test log")
        valid_metadata_dto.logs = [log]

        result = valid_metadata_dto.to_dynamodb_item()

        assert result['videoId']['S'] == 'video123'
        assert result['fileName']['S'] == 'test_video.mp4'
        assert result['totalTime']['N'] == '3600'
        assert 'logs' in result
        assert result['logs']['L'][0]['M']['info']['S'] == 'Test log'

    def test_from_dynamodb_item(self):
        """Testa criação de DTO a partir de item do DynamoDB"""
        item = {
            'videoId': {'S': 'video789'},
            'fileName': {'S': 'from_dynamodb.mp4'},
            'extensionFile': {'S': 'mp4'},
            'status': {'S': 'finished'},
            'created': {'S': '2026-01-27T15:00:00Z'},
            'userId': {'S': 'user789'},
            'totalTime': {'N': '1800'},
            'unitTime': {'S': 's'},
            'startTime': {'N': '0'},
            'endTime': {'N': '30'},
            'timeInterval': {'L': [{'S': '00:00:00'}, {'S': '00:00:30'}]},
            'maxRetry': {'N': '3'},
            'retries': {'N': '0'},
            'quality': {'S': 'high'},
            'logs': {'L': [
                {'M': {
                    'timestamp': {'S': '2026-01-27T15:00:00Z'},
                    'info': {'S': 'Finished'}
                }}
            ]}
        }

        dto = VdscMetadataDTO.from_dynamodb_item(item)

        assert dto.video_id == 'video789'
        assert dto.file_name == 'from_dynamodb.mp4'
        assert dto.total_time == 1800
        assert len(dto.logs) == 1
        assert dto.logs[0].info == 'Finished'

    def test_validate_empty_extension_file(self, valid_metadata_dto):
        """Testa validação com extension_file vazio"""
        valid_metadata_dto.extension_file = ""
        with pytest.raises(ValueError, match="extension_file"):
            valid_metadata_dto.validate()

    def test_validate_empty_status(self, valid_metadata_dto):
        """Testa validação com status vazio"""
        valid_metadata_dto.status = ""
        with pytest.raises(ValueError, match="status"):
            valid_metadata_dto.validate()

    def test_validate_empty_created(self, valid_metadata_dto):
        """Testa validação com created vazio"""
        valid_metadata_dto.created = ""
        with pytest.raises(ValueError, match="created"):
            valid_metadata_dto.validate()

    def test_validate_empty_user_id(self, valid_metadata_dto):
        """Testa validação com user_id vazio"""
        valid_metadata_dto.user_id = ""
        with pytest.raises(ValueError, match="user_id"):
            valid_metadata_dto.validate()

    def test_validate_empty_unit_time(self, valid_metadata_dto):
        """Testa validação com unit_time vazio"""
        valid_metadata_dto.unit_time = ""
        with pytest.raises(ValueError, match="unit_time"):
            valid_metadata_dto.validate()

    def test_validate_empty_quality(self, valid_metadata_dto):
        """Testa validação com quality vazio"""
        valid_metadata_dto.quality = ""
        with pytest.raises(ValueError, match="quality"):
            valid_metadata_dto.validate()

    def test_validate_negative_start_time(self, valid_metadata_dto):
        """Testa validação com start_time negativo"""
        valid_metadata_dto.start_time = -10
        with pytest.raises(ValueError, match="start_time"):
            valid_metadata_dto.validate()

    def test_validate_negative_end_time(self, valid_metadata_dto):
        """Testa validação com end_time negativo"""
        valid_metadata_dto.end_time = -5
        with pytest.raises(ValueError, match="end_time"):
            valid_metadata_dto.validate()

    def test_validate_negative_max_retry(self, valid_metadata_dto):
        """Testa validação com max_retry negativo"""
        valid_metadata_dto.max_retry = -1
        with pytest.raises(ValueError, match="max_retry"):
            valid_metadata_dto.validate()

    def test_validate_time_interval_not_list(self, valid_metadata_dto):
        """Testa validação com time_interval não sendo uma lista"""
        valid_metadata_dto.time_interval = "not a list"
        with pytest.raises(ValueError, match="time_interval"):
            valid_metadata_dto.validate()

    def test_validate_time_interval_with_empty_string(self, valid_metadata_dto):
        """Testa validação com time_interval contendo string vazia"""
        valid_metadata_dto.time_interval = ["00:00:00", ""]
        with pytest.raises(ValueError, match="time_interval"):
            valid_metadata_dto.validate()

    def test_validate_time_interval_with_non_string(self, valid_metadata_dto):
        """Testa validação com time_interval contendo não-string"""
        valid_metadata_dto.time_interval = ["00:00:00", 123]
        with pytest.raises(ValueError, match="time_interval"):
            valid_metadata_dto.validate()

    def test_validate_logs_not_list(self, valid_metadata_dto):
        """Testa validação com logs não sendo uma lista"""
        valid_metadata_dto.logs = "not a list"
        with pytest.raises(ValueError, match="logs"):
            valid_metadata_dto.validate()

    def test_validate_logs_with_invalid_log_entry(self, valid_metadata_dto):
        """Testa validação com logs contendo entrada inválida"""
        invalid_log = LogEntryDTO(timestamp="", info="test")
        valid_metadata_dto.logs = [invalid_log]
        with pytest.raises(ValueError, match="Erro no log"):
            valid_metadata_dto.validate()

    def test_validate_non_integer_total_time(self, valid_metadata_dto):
        """Testa validação com total_time não sendo inteiro"""
        valid_metadata_dto.total_time = "not an integer"
        with pytest.raises(ValueError, match="total_time"):
            valid_metadata_dto.validate()

    def test_to_dict_with_logs(self):
        """Testa conversão para dicionário com logs"""
        log1 = LogEntryDTO(timestamp="2026-01-27T10:00:00Z", info="Log 1")
        log2 = LogEntryDTO(timestamp="2026-01-27T11:00:00Z", info="Log 2")

        dto = VdscMetadataDTO(
            video_id="video999",
            file_name="test_with_logs.mp4",
            extension_file="mp4",
            status="processing",
            created="2026-01-27T10:00:00Z",
            user_id="user999",
            total_time=3600,
            unit_time="s",
            start_time=0,
            end_time=60,
            time_interval=["00:00:00", "00:01:00"],
            max_retry=3,
            retries=1,
            quality="medium",
            logs=[log1, log2]
        )

        result = dto.to_dict()

        assert len(result['logs']) == 2
        assert result['logs'][0]['info'] == 'Log 1'
        assert result['logs'][1]['info'] == 'Log 2'

    def test_roundtrip_to_dict_from_dict(self, valid_metadata_dto):
        """Testa conversão completa: DTO -> dict -> DTO"""
        log = LogEntryDTO(timestamp="2026-01-27T12:00:00Z", info="Roundtrip test")
        valid_metadata_dto.logs = [log]

        # DTO -> dict
        dto_dict = valid_metadata_dto.to_dict()

        # dict -> DTO
        reconstructed_dto = VdscMetadataDTO.from_dict(dto_dict)

        assert reconstructed_dto.video_id == valid_metadata_dto.video_id
        assert reconstructed_dto.file_name == valid_metadata_dto.file_name
        assert reconstructed_dto.total_time == valid_metadata_dto.total_time
        assert len(reconstructed_dto.logs) == 1

    def test_log_entry_validate_whitespace_only(self):
        """Testa LogEntryDTO com apenas espaços em branco"""
        log = LogEntryDTO(timestamp="   ", info="test")
        with pytest.raises(ValueError, match="timestamp"):
            log.validate()

    def test_log_entry_validate_info_whitespace_only(self):
        """Testa LogEntryDTO com info contendo apenas espaços em branco"""
        log = LogEntryDTO(timestamp="2026-01-27T10:00:00Z", info="   ")
        with pytest.raises(ValueError, match="info"):
            log.validate()


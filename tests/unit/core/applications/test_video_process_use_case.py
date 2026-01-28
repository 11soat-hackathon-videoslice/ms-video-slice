"""Testes unitários para VdscProcessUseCase"""
import pytest
import io
import zipfile
from unittest.mock import Mock, MagicMock, patch, call
from src.core.applications.video_process_use_case import VdscProcessUseCase
from src.core.dtos.vdsc_metadata_dto import VdscMetadataDTO
from src.core.enums.vdsc_status_enum import VdscStatusEnum
from src.core.exceptions.vdsc_exceptions import VdscException


@pytest.mark.unit
class TestVdscProcessUseCase:
    """Testes para o caso de uso de processamento de vídeo"""

    @pytest.fixture
    def use_case(self):
        """Fixture do use case"""
        return VdscProcessUseCase()

    @pytest.fixture
    def mock_gateway(self):
        """Fixture do gateway mockado"""
        gateway = Mock()
        gateway.update_metadata_by_video_id = Mock()
        gateway.move_file = Mock()
        gateway.create_directory = Mock()
        gateway.open_file = Mock(return_value=b"fake_video_data")
        gateway.delete_files_by_directory = Mock()
        gateway.delete_file = Mock()
        gateway.save_file = Mock()
        gateway.send_event = Mock()
        gateway.get_list_paths_by_directory = Mock(return_value=[])
        return gateway

    @pytest.fixture
    def mock_config(self):
        """Fixture da configuração"""
        config = Mock()
        config.s3_bucket = {
            "dir_uploads": "uploads/",
            "dir_processing": "processing/",
            "dir_finished": "finished/"
        }
        config.vdsc = {
            "zip_compression_level": 6,
            "png_compression_level": 3,
            "quality": {"high": 720, "medium": 480, "low": 360}
        }
        return config

    @pytest.fixture
    def valid_event_dto(self):
        """Fixture com evento válido"""
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
            time_interval=[10],
            max_retry=3,
            retries=0,
            quality="high",
            logs=[]
        )

    @pytest.fixture
    def mock_handler(self):
        """Fixture do exception handler"""
        handler = Mock()
        handler.vdsc_exception_handler = lambda func: func
        return handler

    def test_get_path_file(self, use_case, mock_config):
        """Testa geração de caminho de arquivo"""
        result = use_case._get_path_file("uploads", "video123", "mp4", mock_config)
        assert result == "uploads/video123.mp4"

    def test_get_path_directory(self, use_case, mock_config):
        """Testa geração de caminho de diretório"""
        result = use_case._get_path_directory("processing", "video123", mock_config)
        assert result == "processing/video123/"

    def test_get_multiplier_time_unit_seconds(self, use_case):
        """Testa multiplicador para segundos"""
        result = use_case._get_multiplier_time_unit("s")
        assert result == 1000

    def test_get_multiplier_time_unit_milliseconds(self, use_case):
        """Testa multiplicador para milissegundos"""
        result = use_case._get_multiplier_time_unit("ms")
        assert result == 1

    def test_get_specific_time_intervals(self, use_case):
        """Testa conversão de intervalos específicos"""
        result = use_case._get_specific_time_intervals([1, 2, 3], 1000)
        assert result == [1000, 2000, 3000]

    def test_get_recurrent_time_intervals(self, use_case):
        """Testa geração de intervalos recorrentes"""
        result = use_case._get_recurrent_time_intervals(0, 30, 10)
        assert result == [0, 10, 20, 30]

    def test_metadata_update_status(self, use_case, valid_event_dto):
        """Testa atualização de status de metadados"""
        from src.core.domain.vdsc_metadata import VdscMetadata, LogEntry
        metadata = VdscMetadata(dto=valid_event_dto)
        log = LogEntry("Teste de log")

        result = use_case._metadata_update_status(metadata, VdscStatusEnum.PROCESSING, log)

        assert result.status == VdscStatusEnum.PROCESSING.value
        assert len(result.logs) == 1

    def test_create_zip_buffer(self, use_case):
        """Testa criação de buffer zip"""
        file_list = [("file1.txt", b"content1"), ("file2.txt", b"content2")]

        result = use_case._create_zip_buffer(file_list, 6)

        assert isinstance(result, io.BytesIO)
        with zipfile.ZipFile(result, 'r') as zf:
            assert "file1.txt" in zf.namelist()
            assert "file2.txt" in zf.namelist()

    def test_get_file_info_list(self, use_case, mock_gateway):
        """Testa obtenção de informações de arquivos"""
        mock_gateway.get_list_paths_by_directory.return_value = [
            "processing/video123/frame1.png",
            "processing/video123/frame2.png"
        ]
        mock_gateway.open_file.side_effect = [b"data1", b"data2"]

        result = use_case._get_file_info_list("processing/video123/", mock_gateway)

        assert len(result) == 2
        assert result[0][0] == "frame1.png"
        assert result[1][0] == "frame2.png"

    def test_create_temporary_file(self, use_case):
        """Testa criação de arquivo temporário"""
        video_data = b"fake_video_data"

        result = use_case._create_temporary_file(video_data, "mp4")

        assert result.endswith(".mp4")
        import os
        assert os.path.exists(result)
        os.remove(result)

    def test_get_target_frame_width(self, use_case):
        """Testa cálculo de largura de frame"""
        import numpy as np
        frame = np.zeros((1080, 1920, 3), dtype=np.uint8)

        result,original = use_case._get_frame_widths(frame, 720)

        assert result == 1280
        assert original == 1920

    def test_get_target_frame_width_no_resize_needed(self, use_case):
        """Testa quando frame já está no tamanho correto"""
        import numpy as np
        frame = np.zeros((1080, 1920, 3), dtype=np.uint8)

        result, original = use_case._get_frame_widths(frame, 1080)

        assert result == original

    def test_frame_resize(self, use_case):
        """Testa redimensionamento de frame"""
        import numpy as np
        frame = np.zeros((1080, 1920, 3), dtype=np.uint8)

        result = use_case._frame_resize(frame, 1280, 720)

        assert result.shape == (720, 1280, 3)

    def test_encode_frame_to_png(self, use_case):
        """Testa codificação de frame para PNG"""
        import numpy as np
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)

        success, data = use_case._encode_frame_to_png(frame, 3)

        assert success is True
        assert data is not None

    def test_create_interval_list_recurrent(self, use_case, valid_event_dto):
        """Testa criação de lista de intervalos recorrentes"""
        from src.core.domain.vdsc_metadata import VdscMetadata
        valid_event_dto.time_interval = [5]
        valid_event_dto.start_time = 0
        valid_event_dto.end_time = 20
        metadata = VdscMetadata(dto=valid_event_dto)

        result = use_case._create_interval_list(metadata, 1000)

        assert result == [0, 5000, 10000, 15000, 20000]

    def test_create_interval_list_specific(self, use_case, valid_event_dto):
        """Testa criação de lista de intervalos específicos"""
        from src.core.domain.vdsc_metadata import VdscMetadata
        valid_event_dto.time_interval = [5, 10, 15]
        metadata = VdscMetadata(dto=valid_event_dto)

        result = use_case._create_interval_list(metadata, 1000)

        assert result == [5000, 10000, 15000]

    def test_compress_images_to_zip(self, use_case, mock_gateway, mock_config):
        """Testa compactação de imagens para zip"""
        mock_gateway.get_list_paths_by_directory.return_value = ["processing/video123/frame1.png"]
        mock_gateway.open_file.return_value = b"fake_image_data"

        use_case._compress_images_to_zip("processing/video123/", "finished/video123.zip", mock_gateway, mock_config)

        mock_gateway.save_file.assert_called_once()

    @patch('cv2.VideoCapture')
    def test_process_video_frames_success(self, mock_video_capture, use_case, mock_gateway, mock_config, valid_event_dto):
        """Testa processamento de frames de vídeo com sucesso"""
        from src.core.domain.vdsc_metadata import VdscMetadata
        import numpy as np

        # Mock do video capture
        mock_cap = MagicMock()
        mock_video_capture.return_value = mock_cap
        mock_cap.read.return_value = (True, np.zeros((1080, 1920, 3), dtype=np.uint8))

        metadata = VdscMetadata(dto=valid_event_dto)
        metadata.unit_time = "s"
        metadata.time_interval = [1]
        metadata.start_time = 0
        metadata.end_time = 5

        use_case._process_video_frames("video123", metadata, b"fake_data", "processing/video123/", mock_gateway, mock_config)

        assert mock_gateway.save_file.called

    @patch('cv2.VideoCapture')
    def test_process_video_frames_failure(self, mock_video_capture, use_case, mock_gateway, mock_config, valid_event_dto):
        """Testa processamento de frames com falha na leitura"""
        from src.core.domain.vdsc_metadata import VdscMetadata

        # Mock do video capture com falha
        mock_cap = MagicMock()
        mock_video_capture.return_value = mock_cap
        mock_cap.read.return_value = (False, None)

        metadata = VdscMetadata(dto=valid_event_dto)
        metadata.time_interval = [1]

        use_case._process_video_frames("video123", metadata, b"fake_data", "processing/video123/", mock_gateway, mock_config)

        # Não deve salvar arquivo se leitura falhar
        assert not mock_gateway.save_file.called

    @patch('cv2.VideoCapture')
    def test_execute_success(self, mock_video_capture, use_case, mock_gateway, mock_config, valid_event_dto, mock_handler):
        """Testa execução completa com sucesso"""
        import numpy as np
        from src.core.domain.vdsc_metadata import VdscMetadata

        # Mock do video capture
        mock_cap = MagicMock()
        mock_video_capture.return_value = mock_cap
        mock_cap.read.return_value = (True, np.zeros((720, 1280, 3), dtype=np.uint8))

        # Mock do update para retornar VdscMetadata
        def mock_update(metadata):
            return metadata
        mock_gateway.update_metadata_by_video_id.side_effect = mock_update
        mock_gateway.get_list_paths_by_directory.return_value = []

        use_case.execute(mock_gateway, valid_event_dto, mock_config, mock_handler)

        assert mock_gateway.update_metadata_by_video_id.called
        assert mock_gateway.move_file.called
        assert mock_gateway.create_directory.called

    def test_execute_with_error_retries_not_exceeded(self, use_case, mock_gateway, mock_config, valid_event_dto, mock_handler):
        """Testa execução com erro quando tentativas não foram excedidas"""
        mock_gateway.move_file.side_effect = Exception("Erro de teste")

        with pytest.raises(VdscException) as exc_info:
            use_case.execute(mock_gateway, valid_event_dto, mock_config, mock_handler)

        assert "Erro ao processar o vídeo ID video123" in str(exc_info.value)
        assert mock_gateway.send_event.called

    def test_execute_with_error_max_retries_reached(self, use_case, mock_gateway, mock_config, valid_event_dto, mock_handler):
        """Testa execução com erro quando máximo de tentativas foi alcançado"""
        valid_event_dto.retries = 3
        valid_event_dto.max_retry = 3
        mock_gateway.move_file.side_effect = Exception("Erro de teste")

        with pytest.raises(VdscException) as exc_info:
            use_case.execute(mock_gateway, valid_event_dto, mock_config, mock_handler)

        assert "Erro ao processar o vídeo ID video123" in str(exc_info.value)

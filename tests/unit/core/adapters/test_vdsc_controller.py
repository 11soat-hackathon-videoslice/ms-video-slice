"""Testes unitários para VdscController"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.core.adapters.vdsc_controller import VdscController
from src.core.dtos.vdsc_metadata_dto import VdscMetadataDTO


@pytest.mark.unit
class TestVdscController:
    """Testes para o controlador"""

    @pytest.fixture
    def mock_dataproxy(self):
        """Mock para DataProxy"""
        return Mock()

    @pytest.fixture
    def mock_handler(self):
        """Mock para ExceptionHandler"""
        return Mock()

    @pytest.fixture
    def controller(self, mock_dataproxy, mock_handler):
        """Fixture para criar instância do controlador"""
        return VdscController(dataproxy=mock_dataproxy, handler=mock_handler)

    @pytest.fixture
    def valid_event_dto(self):
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

    @pytest.fixture
    def mock_config(self):
        """Fixture com configuração mock"""
        return {
            'vdsc': {
                'png_compression_level': 9,
                'zip_compression_level': 5,
                'quality': {
                    'high': 720
                }
            },
            's3_bucket': {
                'dir_uploads': 'uploads/',
                'dir_processing': 'processing/',
                'dir_finished': 'finished/'
            }
        }

    def test_init(self, controller, mock_dataproxy, mock_handler):
        """Testa inicialização do controlador"""
        assert controller.data_proxy == mock_dataproxy
        assert controller.handler == mock_handler

    @patch('src.core.adapters.vdsc_controller.VdscGateway')
    @patch('src.core.adapters.vdsc_controller.VdscProcessUseCase')
    def test_video_slice_processing(self, mock_use_case_class, mock_gateway_class,
                                    controller, valid_event_dto, mock_config):
        """Testa processamento de slice de vídeo"""
        mock_gateway = Mock()
        mock_use_case = Mock()
        mock_gateway_class.return_value = mock_gateway
        mock_use_case_class.return_value = mock_use_case

        controller.video_slice_processing(valid_event_dto, mock_config)

        mock_gateway_class.assert_called_once_with(controller.data_proxy)
        mock_use_case.execute.assert_called_once_with(
            mock_gateway,
            valid_event_dto,
            mock_config,
            controller.handler
        )

    @patch('src.core.adapters.vdsc_controller.VdscGateway')
    @patch('src.core.adapters.vdsc_controller.VdscProcessUseCase')
    def test_video_slice_processing_with_error(self, mock_use_case_class, mock_gateway_class,
                                               controller, valid_event_dto, mock_config):
        """Testa processamento com erro"""
        mock_use_case = Mock()
        mock_use_case_class.return_value = mock_use_case
        mock_use_case.execute.side_effect = Exception("Erro de processamento")

        with pytest.raises(Exception, match="Erro de processamento"):
            controller.video_slice_processing(valid_event_dto, mock_config)

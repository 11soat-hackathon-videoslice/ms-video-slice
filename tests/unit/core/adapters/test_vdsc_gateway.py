"""Testes unitários para VdscGateway"""
import pytest
from unittest.mock import Mock
from src.core.adapters.vdsc_gateway import VdscGateway
from src.core.domain.vdsc_metadata import VdscMetadata
from src.core.dtos.vdsc_metadata_dto import VdscMetadataDTO


@pytest.mark.unit
class TestVdscGateway:
    """Testes para o Gateway"""

    @pytest.fixture
    def mock_dataproxy(self):
        """Mock para DataProxy"""
        return Mock()

    @pytest.fixture
    def gateway(self, mock_dataproxy):
        """Fixture para criar instância do Gateway"""
        return VdscGateway(dataproxy=mock_dataproxy)

    @pytest.fixture
    def valid_dto(self):
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

    def test_init(self, gateway, mock_dataproxy):
        """Testa inicialização do gateway"""
        assert gateway.dataproxy == mock_dataproxy

    def test_create_directory(self, gateway, mock_dataproxy):
        """Testa criação de diretório"""
        gateway.create_directory("test/path/")
        mock_dataproxy.create_directory.assert_called_once_with("test/path/")

    def test_delete_file(self, gateway, mock_dataproxy):
        """Testa deleção de arquivo"""
        gateway.delete_file("test/file.txt")
        mock_dataproxy.delete_file.assert_called_once_with("test/file.txt")

    def test_delete_files_by_directory(self, gateway, mock_dataproxy):
        """Testa deleção de arquivos por diretório"""
        gateway.delete_files_by_directory("test/dir/")
        mock_dataproxy.delete_files_by_directory.assert_called_once_with("test/dir/")

    def test_get_list_paths_by_directory(self, gateway, mock_dataproxy):
        """Testa obtenção de lista de caminhos"""
        mock_dataproxy.get_list_paths_by_directory.return_value = ["file1.txt", "file2.txt"]
        result = gateway.get_list_paths_by_directory("test/dir/")
        assert result == ["file1.txt", "file2.txt"]
        mock_dataproxy.get_list_paths_by_directory.assert_called_once_with("test/dir/")

    def test_move_file(self, gateway, mock_dataproxy):
        """Testa movimentação de arquivo"""
        gateway.move_file("source.txt", "dest.txt")
        mock_dataproxy.move_file.assert_called_once_with("source.txt", "dest.txt")

    def test_open_file(self, gateway, mock_dataproxy):
        """Testa abertura de arquivo"""
        mock_dataproxy.open_file.return_value = b"file content"
        result = gateway.open_file("test/file.txt")
        assert result == b"file content"
        mock_dataproxy.open_file.assert_called_once_with("test/file.txt")

    def test_save_file(self, gateway, mock_dataproxy):
        """Testa salvamento de arquivo"""
        gateway.save_file("test/file.txt", b"content")
        mock_dataproxy.save_file.assert_called_once_with("test/file.txt", b"content")

    def test_update_metadata_by_video_id(self, gateway, mock_dataproxy, valid_dto):
        """Testa atualização de metadados"""
        mock_metadata = VdscMetadata(dto=valid_dto)
        mock_dataproxy.update_metadata_by_video_id.return_value = valid_dto

        result = gateway.update_metadata(mock_metadata)

        assert isinstance(result, VdscMetadata)
        mock_dataproxy.update_metadata_by_video_id.assert_called_once()

"""Testes unitários para S3StorageRepository"""
import pytest
from unittest.mock import Mock, patch
from botocore.exceptions import ClientError
from src.aws.datasources.storage.storage_repository import StorageStorageRepository


@pytest.mark.unit
class TestS3StorageRepository:
    """Testes para o repositório S3"""

    @pytest.fixture
    def mock_s3_client(self):
        """Mock para cliente S3"""
        return Mock()

    @pytest.fixture
    def mock_s3_resource(self):
        """Mock para resource S3"""
        mock_bucket = Mock()
        mock_resource = Mock()
        mock_resource.Bucket.return_value = mock_bucket
        return mock_resource

    @pytest.fixture
    def repository(self, mock_s3_client, mock_s3_resource):
        """Fixture para criar instância do repositório"""
        with patch('boto3.client', return_value=mock_s3_client), \
             patch('boto3.resource', return_value=mock_s3_resource):
            repo = StorageStorageRepository(bucket_name="test-bucket", region="us-east-1")
            repo.s3_client = mock_s3_client
            repo.s3_resource = mock_s3_resource.Bucket("test-bucket")
            return repo

    def test_init(self):
        """Testa inicialização do repositório"""
        with patch('boto3.client') as mock_client, \
             patch('boto3.resource') as mock_resource:
            repo = StorageStorageRepository(bucket_name="test-bucket", region="us-west-2")
            assert repo.bucket_name == "test-bucket"
            assert repo.region == "us-west-2"
            # Os clientes não são criados durante init com lazy loading
            mock_client.assert_not_called()
            mock_resource.assert_not_called()
            # Acessar as properties dispara a criação dos clientes
            _ = repo.s3_client
            _ = repo.s3_resource
            mock_client.assert_called_once_with('s3', region_name='us-west-2')
            mock_resource.assert_called_once_with('s3', region_name='us-west-2')

    def test_delete_file(self, repository, mock_s3_client):
        """Testa deleção de arquivo"""
        repository.delete_file("test/file.txt")
        mock_s3_client.delete_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="test/file.txt"
        )

    def test_delete_file_error(self, repository, mock_s3_client):
        """Testa erro ao deletar arquivo"""
        mock_s3_client.delete_object.side_effect = Exception("S3 error")
        with pytest.raises(Exception):
            repository.delete_file("test/file.txt")

    def test_open_file(self, repository, mock_s3_client):
        """Testa abertura de arquivo"""
        mock_response = {
            'Body': Mock()
        }
        mock_response['Body'].read.return_value = b"file content"
        mock_s3_client.get_object.return_value = mock_response

        result = repository.open_file("test/file.txt")

        assert result == b"file content"
        mock_s3_client.get_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="test/file.txt"
        )

    def test_open_file_error(self, repository, mock_s3_client):
        """Testa erro ao abrir arquivo"""
        mock_s3_client.get_object.side_effect = Exception("S3 error")
        with pytest.raises(Exception):
            repository.open_file("test/file.txt")

    def test_save_file(self, repository, mock_s3_client):
        """Testa salvamento de arquivo"""
        with patch('pathlib.Path') as mock_path:
            mock_file = Mock()
            mock_path.return_value = mock_file
            repository.save_file(file_path="test/file.txt", data=b"content")
            mock_path.assert_called_once_with("test/file.txt")
            mock_file.parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)
            mock_file.write_bytes.assert_called_once_with(b"content")

    def test_save_file_error(self, repository, mock_s3_client):
        """Testa erro ao salvar arquivo"""
        with patch('pathlib.Path') as mock_path:
            mock_file = Mock()
            mock_path.return_value = mock_file
            mock_file.write_bytes.side_effect = Exception("File error")
            with pytest.raises(Exception):
                repository.save_file(file_path="test/file.txt", data=b"content")

    def test_delete_temp_files(self, repository):
        """Testa deleção de arquivos temporários"""
        with patch('shutil.rmtree') as mock_rmtree:
            repository.delete_temp_files("tmp/path")
            mock_rmtree.assert_called_once_with("tmp/path")

    def test_delete_temp_files_error(self, repository):
        """Testa erro ao deletar arquivos temporários"""
        with patch('shutil.rmtree') as mock_rmtree:
            mock_rmtree.side_effect = Exception("rmtree error")
            with pytest.raises(Exception):
                repository.delete_temp_files("tmp/path")

    def test_create_zip_file(self, repository):
        """Testa criação de arquivo ZIP"""
        with patch('pathlib.Path') as mock_path, \
             patch('zipfile.ZipFile') as mock_zipfile:
            mock_dir = Mock()
            mock_file1 = Mock()
            mock_file1.is_file.return_value = True
            mock_file1.name = "file1.txt"
            mock_dir.iterdir.return_value = [mock_file1]
            mock_path.side_effect = [mock_dir, Mock()]  # First for dir_path, second for zip_path
            mock_zip = Mock()
            mock_zipfile.return_value.__enter__.return_value = mock_zip
            repository.create_zip_file("dir/path", "zip/path.zip")
            mock_path.assert_any_call("dir/path")
            mock_path.assert_any_call("zip/path.zip")
            mock_zipfile.assert_called_once()
            mock_zip.write.assert_called_once_with(mock_file1, arcname="file1.txt")

    def test_upload_file(self, repository, mock_s3_client):
        """Testa upload de arquivo"""
        repository.upload_file("source/path", "target/path")
        mock_s3_client.upload_file.assert_called_once_with("source/path", "test-bucket", "target/path")

    def test_upload_file_error(self, repository, mock_s3_client):
        """Testa erro ao fazer upload de arquivo"""
        mock_s3_client.upload_file.side_effect = ClientError({}, "UploadFailed")
        with pytest.raises(ClientError):
            repository.upload_file("source/path", "target/path")

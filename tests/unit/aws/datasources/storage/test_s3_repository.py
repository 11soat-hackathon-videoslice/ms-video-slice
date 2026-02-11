"""Testes unitários para S3StorageRepository"""
import pytest
from unittest.mock import Mock, patch
from botocore.exceptions import ClientError
from src.aws.datasources.storage.s3_repository import S3StorageRepository


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
            repo = S3StorageRepository(bucket_name="test-bucket", region="us-east-1")
            repo.s3_client = mock_s3_client
            repo.s3_resource = mock_s3_resource.Bucket("test-bucket")
            return repo

    def test_init(self):
        """Testa inicialização do repositório"""
        with patch('boto3.client') as mock_client, \
             patch('boto3.resource') as mock_resource:
            repo = S3StorageRepository(bucket_name="test-bucket", region="us-west-2")
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

    def test_create_directory_adds_trailing_slash(self, repository, mock_s3_client):
        """Testa criação de diretório adicionando barra final"""
        repository.create_directory("test/path")
        mock_s3_client.put_object.assert_called_once()
        call_args = mock_s3_client.put_object.call_args
        assert call_args[1]['Key'] == "test/path/"

    def test_create_directory_with_trailing_slash(self, repository, mock_s3_client):
        """Testa criação de diretório que já tem barra final"""
        repository.create_directory("test/path/")
        mock_s3_client.put_object.assert_called_once()
        call_args = mock_s3_client.put_object.call_args
        assert call_args[1]['Key'] == "test/path/"

    def test_create_directory_error(self, repository, mock_s3_client):
        """Testa erro ao criar diretório"""
        mock_s3_client.put_object.side_effect = Exception("S3 error")
        with pytest.raises(Exception):
            repository.create_directory("test/path/")

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

    def test_delete_files_by_directory(self, repository):
        """Testa deleção de arquivos por diretório"""
        mock_collection = Mock()
        mock_collection.delete.return_value = None

        with patch.object(repository, '_get_list_files_in_directory', return_value=mock_collection):
            repository.delete_files_by_directory("test/dir/")
            mock_collection.delete.assert_called_once()

    def test_get_list_paths_by_directory(self, repository):
        """Testa obtenção de lista de caminhos"""
        mock_obj1 = Mock()
        mock_obj1.key = "test/file1.txt"
        mock_obj2 = Mock()
        mock_obj2.key = "test/file2.txt"
        mock_obj3 = Mock()
        mock_obj3.key = "test/subdir/"

        mock_collection = [mock_obj1, mock_obj2, mock_obj3]

        with patch.object(repository, '_get_list_files_in_directory', return_value=mock_collection):
            result = repository.get_list_paths_by_directory("test/")
            assert len(result) == 2
            assert "test/file1.txt" in result
            assert "test/file2.txt" in result
            assert "test/subdir/" not in result

    def test_move_file(self, repository, mock_s3_client):
        """Testa movimentação de arquivo"""
        with patch.object(repository, '_check_file_location', side_effect=[True, False]):
            repository.move_file("source.txt", "destination.txt")

            assert mock_s3_client.copy_object.called
            assert mock_s3_client.delete_object.called

            copy_call_args = mock_s3_client.copy_object.call_args
            assert copy_call_args[1]['Key'] == "destination.txt"

    def test_move_file_skip_when_source_not_found_and_destination_exists(self, repository, mock_s3_client):
        """Testa que não move quando source não existe e destination existe"""
        with patch.object(repository, '_check_file_location', side_effect=[False, True]):
            repository.move_file("source.txt", "destination.txt")

            assert not mock_s3_client.copy_object.called
            assert not mock_s3_client.delete_object.called

    def test_move_file_error(self, repository, mock_s3_client):
        """Testa erro ao mover arquivo"""
        with patch.object(repository, '_check_file_location', side_effect=[True, False]):
            mock_s3_client.copy_object.side_effect = Exception("S3 error")
            with pytest.raises(Exception):
                repository.move_file("source.txt", "destination.txt")

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
        repository.save_file("test/file.txt", b"content")

        mock_s3_client.put_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="test/file.txt",
            Body=b"content"
        )

    def test_save_file_error(self, repository, mock_s3_client):
        """Testa erro ao salvar arquivo"""
        mock_s3_client.put_object.side_effect = Exception("S3 error")
        with pytest.raises(Exception):
            repository.save_file("test/file.txt", b"content")

    def test_check_file_location_exists(self, repository, mock_s3_client):
        """Testa verificação de localização de arquivo quando existe"""
        result = repository._check_file_location("test/file.txt")
        assert result == True
        mock_s3_client.head_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="test/file.txt"
        )

    def test_check_file_location_not_found(self, repository, mock_s3_client):
        """Testa verificação de localização de arquivo quando não encontrado"""
        error = ClientError(
            error_response={'Error': {'Code': '404'}},
            operation_name='HeadObject'
        )
        mock_s3_client.head_object.side_effect = error
        result = repository._check_file_location("test/file.txt")
        assert result == False

    def test_check_file_location_other_error(self, repository, mock_s3_client):
        """Testa verificação de localização de arquivo com outro erro"""
        error = ClientError(
            error_response={'Error': {'Code': '500'}},
            operation_name='HeadObject'
        )
        mock_s3_client.head_object.side_effect = error
        result = repository._check_file_location("test/file.txt")
        assert result == False

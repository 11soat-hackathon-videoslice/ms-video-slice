
"""Testes unitários para S3StorageRepository"""
from unittest.mock import Mock, patch

import pytest

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
        """Testa erro ao deletar arquivo é tratado graciosamente"""
        mock_s3_client.delete_object.side_effect = Exception("S3 error")
        # Não deve lançar exceção, apenas logar o erro
        repository.delete_file("test/file.txt")
        mock_s3_client.delete_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="test/file.txt"
        )

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
        """Testa erro ao deletar arquivos temporários é tratado graciosamente"""
        with patch('shutil.rmtree') as mock_rmtree:
            mock_rmtree.side_effect = Exception("rmtree error")
            # Não deve lançar exceção, apenas logar o erro
            repository.delete_temp_files("tmp/path")
            mock_rmtree.assert_called_once_with("tmp/path")

    def test_create_zipstream(self, repository):
        """Testa criação de zipstream"""
        with patch('pathlib.Path') as mock_path, \
             patch('src.aws.datasources.storage.storage_repository.ZipStream') as mock_zipstream_class, \
             patch('src.aws.datasources.storage.storage_repository.ZIP_DEFLATED', 8):
            mock_dir = Mock()
            mock_file1 = Mock()
            mock_file1.is_file.return_value = True
            mock_file1.name = "file1.txt"
            mock_dir.iterdir.return_value = [mock_file1]
            mock_path.return_value = mock_dir
            mock_zs = Mock()
            mock_zipstream_class.return_value = mock_zs
            result = repository._create_zipstream("dir/path")
            mock_path.assert_called_once_with("dir/path")
            mock_zipstream_class.assert_called_once_with(compress_type=8)
            mock_zs.add_path.assert_called_once_with(mock_file1, arcname="file1.txt")
            assert result == mock_zs

    def test_upload_finished_zip(self, repository, mock_s3_client):
        """Testa upload de zip finalizado"""
        with patch.object(repository, '_create_zipstream') as mock_create_zipstream, \
             patch('src.aws.datasources.storage.storage_repository.StorageZipStreamReader') as mock_reader:
            mock_zs = Mock()
            mock_create_zipstream.return_value = mock_zs
            mock_reader_instance = Mock()
            mock_reader.return_value = mock_reader_instance
            repository.upload_finished_zip("output/dir", "target/path.zip")
            mock_create_zipstream.assert_called_once_with("output/dir")
            mock_reader.assert_called_once_with(mock_zs)
            mock_s3_client.upload_fileobj.assert_called_once_with(
                Fileobj=mock_reader_instance,
                Bucket="test-bucket",
                Key="target/path.zip"
            )

    def test_upload_finished_zip_error(self, repository, mock_s3_client):
        """Testa erro ao fazer upload de zip finalizado"""
        with patch.object(repository, '_create_zipstream') as mock_create_zipstream:
            mock_create_zipstream.side_effect = Exception("Zip error")
            with pytest.raises(Exception):
                repository.upload_finished_zip("output/dir", "target/path.zip")

    def test_s3_client_lazy_loading(self):
        """Testa que o cliente S3 é criado apenas no primeiro acesso"""
        with patch('boto3.client') as mock_client:
            repo = StorageStorageRepository(bucket_name="test-bucket", region="us-east-1")

            # Ainda não deve ter criado o cliente
            assert repo._s3_client is None
            mock_client.assert_not_called()

            # Primeiro acesso cria o cliente
            _ = repo.s3_client
            mock_client.assert_called_once_with('s3', region_name='us-east-1')

            # Segundo acesso reutiliza o mesmo cliente
            _ = repo.s3_client
            mock_client.assert_called_once()  # Ainda apenas uma chamada

    def test_s3_resource_lazy_loading(self):
        """Testa que o resource S3 é criado apenas no primeiro acesso"""
        with patch('boto3.resource') as mock_resource:
            mock_bucket = Mock()
            mock_resource.return_value.Bucket.return_value = mock_bucket

            repo = StorageStorageRepository(bucket_name="test-bucket", region="us-east-1")

            # Ainda não deve ter criado o resource
            assert repo._s3_resource is None
            mock_resource.assert_not_called()

            # Primeiro acesso cria o resource
            _ = repo.s3_resource
            mock_resource.assert_called_once_with('s3', region_name='us-east-1')

            # Segundo acesso reutiliza o mesmo resource
            _ = repo.s3_resource
            mock_resource.assert_called_once()  # Ainda apenas uma chamada

    def test_s3_client_setter(self):
        """Testa setter do cliente S3 para mocking"""
        repo = StorageStorageRepository(bucket_name="test-bucket", region="us-east-1")
        mock_client = Mock()

        repo.s3_client = mock_client

        assert repo._s3_client == mock_client
        assert repo.s3_client == mock_client

    def test_s3_resource_setter(self):
        """Testa setter do resource S3 para mocking"""
        repo = StorageStorageRepository(bucket_name="test-bucket", region="us-east-1")
        mock_resource = Mock()

        repo.s3_resource = mock_resource

        assert repo._s3_resource == mock_resource
        assert repo.s3_resource == mock_resource

    def test_check_disk_space(self, repository):
        """Testa verificação de espaço em disco"""
        with patch('shutil.disk_usage') as mock_disk_usage, \
             patch('tempfile.gettempdir', return_value='/tmp'):
            mock_disk_usage.return_value = (1000000000, 500000000, 500000000)  # total, used, free

            # Método não retorna nada, apenas loga
            result = repository._check_disk_space()

            assert result is None
            mock_disk_usage.assert_called_once_with('/tmp')

    def test_get_dir_size(self, repository):
        """Testa cálculo do tamanho de um diretório"""
        with patch('os.scandir') as mock_scandir:
            # Mock de entradas do diretório
            mock_entry1 = Mock()
            mock_entry1.is_file.return_value = True
            mock_entry1.stat.return_value.st_size = 1024

            mock_entry2 = Mock()
            mock_entry2.is_file.return_value = True
            mock_entry2.stat.return_value.st_size = 2048

            mock_entry3 = Mock()
            mock_entry3.is_file.return_value = False  # Diretório, não conta

            mock_scandir.return_value.__enter__.return_value = [mock_entry1, mock_entry2, mock_entry3]

            repository._get_dir_size('/test/path')

            mock_scandir.assert_called_once_with('/test/path')

    def test_create_zipstream_error(self, repository):
        """Testa erro ao criar zipstream"""
        with patch('pathlib.Path') as mock_path:
            mock_path.return_value.iterdir.side_effect = Exception("Directory error")

            with pytest.raises(Exception, match="Directory error"):
                repository._create_zipstream("invalid/path")

    def test_create_zipstream_with_subdirectories(self, repository):
        """Testa criação de zipstream ignorando subdiretórios"""
        with patch('pathlib.Path') as mock_path, \
             patch('src.aws.datasources.storage.storage_repository.ZipStream') as mock_zipstream_class, \
             patch('src.aws.datasources.storage.storage_repository.ZIP_DEFLATED', 8):

            mock_dir = Mock()

            # Mock de arquivo
            mock_file = Mock()
            mock_file.is_file.return_value = True
            mock_file.name = "file1.txt"

            # Mock de subdiretório (não deve ser adicionado)
            mock_subdir = Mock()
            mock_subdir.is_file.return_value = False

            mock_dir.iterdir.return_value = [mock_file, mock_subdir]
            mock_path.return_value = mock_dir

            mock_zs = Mock()
            mock_zipstream_class.return_value = mock_zs

            result = repository._create_zipstream("dir/path")

            # Apenas o arquivo deve ser adicionado, não o subdiretório
            mock_zs.add_path.assert_called_once_with(mock_file, arcname="file1.txt")
            assert result == mock_zs

    def test_upload_finished_zip_with_upload_error(self, repository, mock_s3_client):
        """Testa erro durante upload para S3"""
        with patch.object(repository, '_create_zipstream') as mock_create_zipstream, \
             patch('src.aws.datasources.storage.storage_repository.StorageZipStreamReader'):
            mock_create_zipstream.return_value = Mock()
            mock_s3_client.upload_fileobj.side_effect = Exception("S3 upload error")

            with pytest.raises(Exception, match="S3 upload error"):
                repository.upload_finished_zip("output/dir", "target/path.zip")


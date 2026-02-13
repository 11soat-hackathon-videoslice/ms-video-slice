import logging
import zipfile

import boto3
from botocore.exceptions import ClientError

from .storage_interface import StorageInterface

logger = logging.getLogger(__name__)

class StorageStorageRepository(StorageInterface):
    """Repositório para operações de armazenamento no Amazon S3"""

    def __init__(self, bucket_name: str, region: str):
        """Inicializa o repositório S3 com bucket e região específicos"""
        self.bucket_name = bucket_name
        self.region = region
        self._s3_client = None
        self._s3_resource = None

    @property
    def s3_client(self):
        """Lazy loading do cliente boto3 S3"""
        if self._s3_client is None:
            self._s3_client = boto3.client('s3', region_name=self.region)
        return self._s3_client

    @s3_client.setter
    def s3_client(self, value):
        """Setter para permitir mock do cliente nos testes"""
        self._s3_client = value

    @property
    def s3_resource(self):
        """Lazy loading do recurso boto3 S3"""
        if self._s3_resource is None:
            self._s3_resource = boto3.resource('s3', region_name=self.region).Bucket(self.bucket_name)
        return self._s3_resource

    @s3_resource.setter
    def s3_resource(self, value):
        """Setter para permitir mock do recurso nos testes"""
        self._s3_resource = value

    def delete_file(self, file_path: str) -> None:
        """Remove um arquivo do S3"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name,Key=file_path)
            logger.info(f"Arquivo deletado com sucesso: s3://{self.bucket_name}/{file_path}")
        except Exception as e:
            logger.error(f"Erro ao deletar arquivo {file_path}: {str(e)}", exc_info=True)
            raise

    def delete_temp_files(self, tmp_path:str) -> None:
        """Deleta arquivos temporários localmente"""
        import shutil
        try:
            shutil.rmtree(tmp_path)
            logger.info(f"Arquivos temporários deletados com sucesso: {tmp_path}")
        except Exception as e:
            logger.error(f"Erro ao deletar arquivos temporários {tmp_path}: {str(e)}", exc_info=True)
            raise

    def open_file(self, file_path: str) -> bytes:
        """Lê e retorna o conteúdo de um arquivo do S3"""
        try:

            response = self.s3_client.get_object(Bucket=self.bucket_name,Key=file_path)
            data = response['Body'].read()
            logger.info(f"Arquivo lido com sucesso: s3://{self.bucket_name}/{file_path}")
            return data

        except Exception as e:
            logger.error(f"Erro ao ler arquivo {file_path}: {str(e)}", exc_info=True)
            raise

    def save_file(self, file_path: str, data: bytes) -> None:
        import pathlib
        path = pathlib.Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            path.write_bytes(data)
            logger.info(f"Arquivo salvo localmente com sucesso: {file_path}")
        except Exception as e:
            logger.error(f"Erro ao salvar arquivo localmente {file_path}: {str(e)}", exc_info=True)
            raise

    def create_zip_file(self, directory_path: str, zip_file_path: str) -> None:
        """Cria um arquivo ZIP no temporário e faz upload para o S3"""
        from pathlib import Path

        dir_path = Path(directory_path)
        zip_path = Path(zip_file_path)

        with zipfile.ZipFile(zip_path, 'w', allowZip64=True) as zip_file:
            for file in dir_path.iterdir():
                if file.is_file():
                    # O zipfile aceita objetos Path diretamente
                    zip_file.write(file, arcname=file.name)
        logger.info(f"Arquivo ZIP criado com sucesso: {zip_path}")

    def upload_file(self, source_path: str, target_path: str) -> None:
        try:
            self.s3_client.upload_file(source_path, self.bucket_name, target_path)
            logger.info(f"Arquivo ZIP enviado para S3 com sucesso: s3://{self.bucket_name}/{target_path}")
        except ClientError as e:
            logger.error(f"Erro ao enviar arquivo ZIP para S3: {str(e)}", exc_info=True)
            raise
import logging
import os

import boto3
from zipstream import ZipStream, ZIP_DEFLATED
from .storage_interface import StorageInterface
from .storage_zipstream import StorageZipStreamReader

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

    def delete_temp_files(self, tmp_path:str) -> None:
        """Deleta arquivos temporários localmente"""
        import shutil
        try:
            shutil.rmtree(tmp_path)
            logger.info(f"Arquivos temporários deletados com sucesso: {tmp_path}")
        except Exception as e:
            logger.error(f"Erro ao deletar arquivos temporários {tmp_path}: {str(e)}", exc_info=True)

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
        self._check_disk_space()
        path = pathlib.Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            path.write_bytes(data)
            logger.info(f"Arquivo salvo localmente com sucesso: {file_path}")
        except Exception as e:
            logger.error(f"Erro ao salvar arquivo localmente {file_path}: {str(e)}", exc_info=True)
            raise

    def upload_finished_zip(self, output_directory: str, target_path: str) -> None:
        zip_stream = self._create_zipstream(output_directory)
        try:
            self.s3_client.upload_fileobj(
                Fileobj=StorageZipStreamReader(zip_stream),
                Bucket=self.bucket_name,
                Key=target_path
            )
            logger.info(f"Arquivo enviado para S3 com sucesso: s3://{self.bucket_name}/{target_path}")
        except Exception as e:
            logger.error(f"Erro ao enviar arquivo para S3 {target_path}: {str(e)}", exc_info=True)
            raise

    def _create_zipstream(self, output_directory: str):
        """Cria zipStream a partir dos arquivos num diretório local para upload dinamico"""
        from pathlib import Path

        dir_path = Path(output_directory)
        logger.debug(f"Diretório dos arquivos: {dir_path}")
        zs = ZipStream(compress_type=ZIP_DEFLATED)
        try:
            for file in dir_path.iterdir():
                if file.is_file():
                    zs.add_path(file, arcname=file.name)
            return zs
        except Exception as e:
            logger.error(f"Erro ao criar zipStream do diretório {output_directory}: {str(e)}", exc_info=True)
            raise

    #### debugging methods ####
    def _check_disk_space(self) -> bool:
        """Verifica se há espaço suficiente no disco local para processar o vídeo"""
        import shutil
        import tempfile
        temp_dir = tempfile.gettempdir()
        total, used, free = shutil.disk_usage(temp_dir)
        logger.debug(f"Espaço em disco - Total: {total} bytes, Usado: {used} bytes, Livre: {free} bytes")

    def _get_dir_size(self, path: str):
        total = 0
        with os.scandir(path) as it:
            for entry in it:
                if entry.is_file():
                    total += entry.stat().st_size
        logger.debug(f"Tamanho do diretório: {total} em bytes")
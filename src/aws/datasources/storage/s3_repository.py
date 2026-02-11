import logging
import boto3
from botocore.exceptions import ClientError

from .s3_interface import S3Interface
from boto3.resources.collection import ResourceCollection

logger = logging.getLogger(__name__)

class S3StorageRepository(S3Interface):
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

    def create_directory(self, directory_path: str) -> None:
        """Cria um diretório (prefixo) no S3"""
        if not directory_path.endswith('/'):
            directory_path += '/'

        try:

            self.s3_client.put_object(Bucket=self.bucket_name,Key=directory_path,Body=b'')
            logger.info(f"Diretório criado com sucesso: s3://{self.bucket_name}/{directory_path}")

        except Exception as e:
            logger.error(f"Erro ao criar diretório {directory_path}: {str(e)}", exc_info=True)
            raise

    def delete_file(self, file_path: str) -> None:
        """Remove um arquivo do S3"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name,Key=file_path)
            logger.info(f"Arquivo deletado com sucesso: s3://{self.bucket_name}/{file_path}")
        except Exception as e:
            logger.error(f"Erro ao deletar arquivo {file_path}: {str(e)}", exc_info=True)
            raise


    def delete_files_by_directory(self, directory_path: str) -> None:
        """Remove todos os arquivos de um diretório no S3"""
        try:

            self._get_list_files_in_directory(directory_path).delete()
            logger.info(f"Arquivos do diretório deletados com sucesso: s3://{self.bucket_name}/{directory_path}")

        except Exception as e:
            logger.error(f"Erro ao deletar arquivos do diretório {directory_path}: {str(e)}", exc_info=True)
            raise

    def get_list_paths_by_directory(self, directory_path: str) -> list[str]:
        """Obtém lista de caminhos de arquivos em um diretório do S3"""
        try:
            list_files = self._get_list_files_in_directory(directory_path)
            file_paths = [obj.key for obj in list_files if not obj.key.endswith('/')]
            logger.info(f"Lista de arquivos obtida com sucesso do diretório: s3://{self.bucket_name}/{directory_path}")
            return file_paths

        except Exception as e:
            logger.error(f"Erro ao listar arquivos do diretório {directory_path}: {str(e)}", exc_info=True)
            raise


    def move_file(self, source_path: str, destination_path: str) -> None:
        if self._check_file_location(source_path) == False and self._check_file_location(destination_path) == True:
            logger.warning(f"Video localizado em s3://{self.bucket_name}/{destination_path} e não localizado em s3://{self.bucket_name}/{source_path}. Pulando etapa de movimentação.")
            return None
        try:
                copy_source = {'Bucket': self.bucket_name,'Key': source_path}
                self.s3_client.copy_object(CopySource=copy_source,Bucket=self.bucket_name,Key=destination_path)
                self.s3_client.delete_object(Bucket=self.bucket_name,Key=source_path)
                logger.info(f"Arquivo movido de s3://{self.bucket_name}/{source_path} para s3://{self.bucket_name}/{destination_path}")

        except Exception as e:
            logger.error(f"Erro ao mover arquivo de {source_path} para {destination_path}: {str(e)}", exc_info=True)
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
        """Salva um arquivo no S3"""
        try:
            self.s3_client.put_object(Bucket=self.bucket_name,Key=file_path,Body=data)
            logger.info(f"Arquivo salvo com sucesso: s3://{self.bucket_name}/{file_path}")
        except Exception as e:
            logger.error(f"Erro ao salvar arquivo {file_path}: {str(e)}", exc_info=True)
            raise

    def _check_file_location(self, file_path: str) -> bool:
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=file_path)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == "404":
                logger.warning(f"Não encontrado arquivo em s3://{self.bucket_name}/{file_path}")
            return False


    def _get_list_files_in_directory(self, directory_path: str) -> ResourceCollection:
        """Obtém lista de arquivos em um diretório do S3"""
        try:
            return self.s3_resource.objects.filter(Prefix=directory_path)

        except Exception as e:
            logger.error(f"Erro ao listar arquivos do diretório {directory_path}: {str(e)}", exc_info=True)
            raise


from ...core.interfaces.vdsc_dataproxy_interface import VdscDataProxyInterface
from ...core.dtos.vdsc_metadata_dto import VdscMetadataDTO
from ..datasources.database.dynamodb_interface import DynamoDBInterface
from ..datasources.storage.s3_interface import S3Interface
from ..datasources.producer.event_producer_interface import EventProducerInterface

class VdscDataProxy(VdscDataProxyInterface):

    def __init__(self, dynamodb: DynamoDBInterface, s3: S3Interface, event_producer: EventProducerInterface):
        self.dynamodb = dynamodb
        self.s3 = s3
        self.event_producer = event_producer

    def create_directory(self, directory_path: str) -> None:
        self.s3.create_directory(directory_path)

    def delete_file(self, file_path: str) -> None:
        self.s3.delete_file(file_path)

    def delete_files_by_directory(self, directory_path: str) -> None:
        self.s3.delete_files_by_directory(directory_path)

    def get_list_paths_by_directory(self, directory_path: str) -> list[str]:
        return self.s3.get_list_paths_by_directory(directory_path)

    def open_file(self, file_path: str) -> bytes:
        return self.s3.open_file(file_path)

    def move_file(self, source_path: str, destination_path: str) -> None:
        self.s3.move_file(source_path, destination_path)

    def save_file(self, file_path: str, data: bytes) -> None:
        self.s3.save_file(file_path, data)

    def send_event(self, event_data: dict) -> None:
        self.event_producer.send_event(event_data)

    def update_metadata_by_video_id(self, update_data: VdscMetadataDTO) -> VdscMetadataDTO:
        """Atualiza metadados recebendo e retornando DTO"""
        return self.dynamodb.update_metadata_by_video_id(update_data)

def dict_to_dynamodb_format(data: dict) -> dict:
    dynamodb_data = {}
    for key, value in data.items():
        if isinstance(value, bool):
            dynamodb_data[key] = {'BOOL': value}
        elif isinstance(value, str):
            dynamodb_data[key] = {'S': value}
        elif isinstance(value, int):
            dynamodb_data[key] = {'N': str(value)}
        elif isinstance(value, float):
            dynamodb_data[key] = {'N': str(value)}
        elif isinstance(value, list):
            dynamodb_data[key] = {'L': [dict_to_dynamodb_format({'value': v})['value'] for v in value]}
        elif isinstance(value, dict):
            dynamodb_data[key] = {'M': dict_to_dynamodb_format(value)}
        elif value is None:
            dynamodb_data[key] = {'NULL': True}
    return dynamodb_data
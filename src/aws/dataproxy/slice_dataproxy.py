import datetime

from aws.datasources.metrics.cloudwatch_interface import CloudWatchInterface
from core.interfaces.slice.slice_dataproxy_interface import SliceDataProxyInterface
from core.dtos.vdsc_metadata_dto import VdscMetadataDTO
from core.dtos.notification_dto import NotificationDto
from aws.datasources.database.dynamodb_interface import DynamoDBInterface
from aws.datasources.storage.storage_interface import StorageInterface
from aws.datasources.producer.event_producer_interface import EventProducerInterface

class SliceDataProxy(SliceDataProxyInterface):



    def __init__(self, dynamodb: DynamoDBInterface, storage: StorageInterface, event_producer: EventProducerInterface, cloudwatch: CloudWatchInterface):
        self.dynamodb = dynamodb
        self.storage = storage
        self.event_producer = event_producer
        self.cloudwatch = cloudwatch

    def delete_file(self, file_path: str) -> None:
        self.storage.delete_file(file_path)

    def open_file(self, file_path: str) -> bytes:
        return self.storage.open_file(file_path)

    def save_file(self, file_path: str, data: bytes) -> None:
        self.storage.save_file(file_path, data)

    def send_schedule_retry_event(self, vdsc_metadata: VdscMetadataDTO, schedule_time: datetime, schedule_config: dict) -> None:
        self.event_producer.send_schedule_retry_event(vdsc_metadata.to_dynamodb_item(), schedule_time, schedule_config)

    def send_metric(self, metric_info: str) -> None:
        self.cloudwatch.send_metric(metric_info)

    def send_notification(self, notification: NotificationDto) -> None:
        self.event_producer.send_notification(notification)

    def upload_finished_zip(self, output_directory: str, target_path: str) -> None:
        self.storage.upload_finished_zip(output_directory, target_path)

    def update_metadata_by_video_id(self, update_data: VdscMetadataDTO) -> VdscMetadataDTO:
        """Atualiza metadados recebendo e retornando DTO"""
        return self.dynamodb.update_metadata_by_video_id(update_data)

    def delete_temp_files(self, dir_tmp:str) -> None:
        self.storage.delete_temp_files(dir_tmp)

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
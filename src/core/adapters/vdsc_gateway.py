import datetime

from ..interfaces.vdsc_gateway_interface import VdscGatewayInferface
from ..interfaces.vdsc_dataproxy_interface import VdscDataProxyInterface
from ..dtos.vdsc_metadata_dto import VdscMetadataDTO
from ..domain.vdsc_metadata import VdscMetadata

class VdscGateway(VdscGatewayInferface):

    def __init__(self, dataproxy: VdscDataProxyInterface):
        self.dataproxy = dataproxy

    def create_directory(self, directory_path: str) -> None:
        self.dataproxy.create_directory(directory_path)

    def delete_file(self, file_path: str) -> None:
        self.dataproxy.delete_file(file_path)

    def delete_files_by_directory(self, directory_path: str) -> None:
        self.dataproxy.delete_files_by_directory(directory_path)

    def get_list_paths_by_directory(self, directory_path: str) -> list[str]:
        return self.dataproxy.get_list_paths_by_directory(directory_path)

    def move_file(self, source_path: str, destination_path: str) -> None:
        self.dataproxy.move_file(source_path, destination_path)

    def open_file(self, file_path: str) -> bytes:
        return self.dataproxy.open_file(file_path)

    def save_file(self, file_path: str, data: bytes) -> None:
        self.dataproxy.save_file(file_path, data)

    def send_schedule_retry_event(self, vdsc_metadata: VdscMetadata, schedule_time: datetime, schedule_config: dict) -> None:
        event_metadata = VdscMetadataDTO.from_dict(vdsc_metadata.to_dict())
        self.dataproxy.send_schedule_retry_event(event_metadata, schedule_time, schedule_config)

    def send_notification(self, vdsc_metadata: VdscMetadata, channels: list[str], message: str) -> None:
        pass

    def update_metadata(self, update_data: VdscMetadata) -> VdscMetadata:
        """Atualiza metadados convertendo a entidade de domínio para DTO"""
        # Converter entidade de domínio para dict e depois para DTO
        update_data_dto = VdscMetadataDTO.from_dict(update_data.to_dict())
        # Atualizar via dataproxy
        updated_dto = self.dataproxy.update_metadata_by_video_id(update_data_dto)
        # Converter DTO de volta para entidade de domínio
        return VdscMetadata(dto=updated_dto)


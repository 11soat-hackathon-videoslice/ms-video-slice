import datetime
from abc import ABC, abstractmethod
from ..domain.vdsc_metadata import VdscMetadata

class VdscGatewayInferface(ABC):

    @abstractmethod
    def create_directory(self, directory_path: str) -> None:
        pass

    @abstractmethod
    def delete_file(self, file_path: str) -> None:
        pass

    @abstractmethod
    def delete_files_by_directory(self, directory_path: str) -> None:
        pass

    @abstractmethod
    def get_list_paths_by_directory(self, directory_path: str) -> list[str]:
        pass

    @abstractmethod
    def move_file(self, source_path: str, destination_path: str) -> None:
        pass

    @abstractmethod
    def open_file(self, file_path: str) -> bytes:
        pass

    @abstractmethod
    def save_file(self, file_path: str, data: bytes) -> None:
        pass

    @abstractmethod
    def send_schedule_retry_event(self, vdsc_metadata: VdscMetadata, schedule_time: datetime, schedule_config: dict) -> None:
        pass

    @abstractmethod
    def send_notification(self, vdsc_metadata:VdscMetadata, channels: list[str], message: str) -> None:
        pass

    @abstractmethod
    def update_metadata(self, update_data: VdscMetadata) -> VdscMetadata:
        pass






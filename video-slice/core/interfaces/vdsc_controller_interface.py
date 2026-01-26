from abc import ABC, abstractmethod
from ..dtos.vdsc_metadata_dto import VdscMetadataDTO
from ..interfaces.vdsc_dataproxy_interface import VdscDataProxyInterface

class VdscControllerInterface(ABC):

        @abstractmethod
        def video_slice_processing(self, event: VdscMetadataDTO, config: dict) -> dict:
            pass
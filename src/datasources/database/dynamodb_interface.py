from abc import ABC, abstractmethod
from core.dtos.vdsc_metadata_dto import VdscMetadataDTO

class DynamoDBInterface(ABC):

    @abstractmethod
    def update_metadata_by_video_id(self, update_data: VdscMetadataDTO) -> VdscMetadataDTO:
        """Atualiza os metadados de um vídeo no DynamoDB recebendo e retornando DTO"""
        pass


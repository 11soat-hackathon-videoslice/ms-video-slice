"""Data Transfer Objects para Event."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class EventDTO:
    """DTO para criação de Event."""
    timestamp: str
    video_id: str
    extension_file: str
    engine: str
    status: str
    message: str

    def to_dict(self) -> dict:
        """Converte o DTO para dicionário."""
        return {
            "timestamp": self.timestamp,
            "videoId": self.video_id,
            "extensionFile": self.extension_file,
            "engine": self.engine,
            "status": self.status,
            "message": self.message
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'EventDTO':
        """Cria DTO a partir de um dicionário."""
        return cls(
            timestamp=data['timestamp'],
            video_id=data['videoId'],
            extension_file=data['extensionFile'],
            engine=data['engine'],
            status=data['status'],
            message=data['message']
        )

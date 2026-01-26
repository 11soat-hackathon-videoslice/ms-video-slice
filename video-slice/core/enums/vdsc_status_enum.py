"""Enumeração de status de processamento de vídeo."""
from enum import Enum


class VdscStatusEnum(str, Enum):
    """Enumeração para status de processamento de metadados de slice de vídeo."""
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    FINISHED = "FINISHED"
    RETRYING = "RETRYING"
    FAILED = "FAILED"
    ERROR = "ERROR"

    def __str__(self) -> str:
        """Retorna o valor do enum como string."""
        return self.value

    @classmethod
    def is_valid(cls, status: str) -> bool:
        """Verifica se uma string de status é válida."""
        return status in [s.value for s in cls]

    @classmethod
    def get_all_values(cls) -> list:
        """Obtém todos os valores de status válidos."""
        return [s.value for s in cls]

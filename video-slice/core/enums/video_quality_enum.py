"""Enumeração de qualidade de vídeo para captura de frames."""
from enum import Enum


class VideoQuality(str, Enum):
    """Enumeração para níveis de qualidade de vídeo usados na captura de frames.

    Valores representam configurações de qualidade para processamento de vídeo:
    - ULTRA: Qualidade máxima (100%)
    - HIGH: Qualidade alta (75%)
    - MEDIUM: Qualidade média (50%)
    - LOW: Qualidade baixa (25%)
    """

    ULTRA = "ultra"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    def __str__(self) -> str:
        """Retorna o valor do enum como string."""
        return self.value

    @classmethod
    def is_valid(cls, quality: str) -> bool:
        """Verifica se uma string de qualidade é válida."""
        return quality in [q.value for q in cls]

    @classmethod
    def get_all_values(cls) -> list:
        """Obtém todos os valores de qualidade válidos."""
        return [q.value for q in cls]

    def get_scale_factor(self) -> str:
        """Obtém o fator de escala para processamento de vídeo."""
        return self.value

    @classmethod
    def from_scale(cls, scale: str) -> 'VideoQuality':
        """Obtém VideoQuality a partir de um fator de escala.

        Args:
            scale: Fator de escala (string: "ultra", "high", "medium", "low")

        Returns:
            Enum VideoQuality correspondente à escala

        Raises:
            ValueError: Se o fator de escala não for válido
        """
        for quality in cls:
            if quality.value == scale:
                return quality
        raise ValueError(f"Fator de escala inválido: {scale}")

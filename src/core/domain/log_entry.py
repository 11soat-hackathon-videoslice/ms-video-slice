"""Entidade de domínio de entrada de log."""
from datetime import datetime, UTC
from typing import Optional


class LogEntry:
    """Entidade de domínio representando uma entrada de log."""

    def __init__(self, info: str, timestamp: Optional[datetime] = None):
        """Inicializa LogEntry com timestamp no formato ISO 8601"""
        if timestamp is None:
            timestamp = datetime.now(UTC)
        self.timestamp = timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
        self.info = info

    def to_dict(self) -> dict:
        """Converte para representação em dicionário."""
        return {
            "timestamp": self.timestamp,
            "info": self.info
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'LogEntry':
        """Cria LogEntry a partir de um dicionário."""
        timestamp_str = data.get('timestamp')
        timestamp = None
        if timestamp_str:
            # Remove sufixo 'Z' se presente
            timestamp_str = timestamp_str.rstrip('Z')
            timestamp = datetime.fromisoformat(timestamp_str)

        return cls(
            info=data['info'],
            timestamp=timestamp
        )

    def __repr__(self) -> str:
        return f"LogEntry(timestamp={self.timestamp}, info='{self.info}')"

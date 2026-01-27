"""Video Slice Metadata domain entity."""
from typing import List, Optional
from datetime import datetime, UTC
from .log_entry import LogEntry
from ..enums.vdsc_status_enum import VdscStatusEnum
from ..enums.video_quality_enum import VideoQuality
from ..dtos.vdsc_metadata_dto import VdscMetadataDTO


class VdscMetadata:
    def __init__(
        self,
        dto: VdscMetadataDTO,
        logs: Optional[List[LogEntry]] = None
    ):
        self.video_id = dto.video_id
        self.file_name = dto.file_name
        self.extension_file = dto.extension_file
        self.status = dto.status
        # Converter created para datetime se for string
        if isinstance(dto.created, str):
            self.created = datetime.fromisoformat(dto.created.replace('Z', '+00:00'))
        else:
            self.created = dto.created
        self.user_id = dto.user_id
        self.total_time = dto.total_time
        self.unit_time = dto.unit_time
        self.start_time = dto.start_time
        self.end_time = dto.end_time
        self.time_interval = dto.time_interval if dto.time_interval else []
        self.max_retry = dto.max_retry
        self.retries = dto.retries
        self.quality = dto.quality
        self.logs = dto.logs if dto.logs else []

    def validate(self) -> bool:
        """Valida as regras de negócio para metadados de slice de vídeo."""
        if not self.video_id or not self.user_id:
            raise ValueError("ID do vídeo e ID do usuário são obrigatórios")

        if not self.file_name:
            raise ValueError("Nome do arquivo é obrigatório")

        if not self.extension_file:
            raise ValueError("Extensão do arquivo é obrigatória")

        if self.total_time <= 0:
            raise ValueError("Tempo total deve ser maior que zero")

        if self.start_time < 0:
            raise ValueError("Tempo inicial não pode ser negativo")

        if self.end_time <= self.start_time:
            raise ValueError("Tempo final deve ser maior que o tempo inicial")

        if self.end_time > self.total_time:
            raise ValueError("Tempo final não pode exceder o tempo total")

        if self.max_retry < 0:
            raise ValueError("Número máximo de tentativas não pode ser negativo")

        if self.retries < 0:
            raise ValueError("Número de tentativas não pode ser negativo")

        if self.retries > self.max_retry:
            raise ValueError("Número de tentativas não pode exceder o máximo permitido")

        if self.unit_time not in ["s", "ms", "m", "h"]:
            raise ValueError("Unidade de tempo deve ser uma das seguintes: s, ms, m, h")

        if not VideoQuality.is_valid(self.quality):
            valid_qualities = VideoQuality.get_all_values()
            raise ValueError(f"Qualidade deve ser uma das seguintes: {', '.join(valid_qualities)}")

        if not VdscStatusEnum.is_valid(self.status):
            valid_statuses = VdscStatusEnum.get_all_values()
            raise ValueError(f"Status deve ser um dos seguintes: {', '.join(valid_statuses)}")

        return True

    def add_log(self, info: str, timestamp: Optional[datetime] = None):
        """Adiciona uma entrada de log aos metadados."""
        log_entry = LogEntry(info=info, timestamp=timestamp)
        self.logs.append(log_entry)

    def _update_status(self, new_status: str, log_info: str):
        """Atualiza o status dos metadados e adiciona uma entrada de log."""
        self.status = new_status
        self.add_log(log_info)

    def mark_as_uploaded(self):
        """Marca os metadados como enviado."""
        self._update_status(VdscStatusEnum.UPLOADED.value, "uploaded")

    def mark_as_processing(self):
        """Marca os metadados como em processamento."""
        self._update_status(VdscStatusEnum.PROCESSING.value, "processing")

    def mark_as_finished(self):
        """Marca os metadados como finalizado."""
        self._update_status(VdscStatusEnum.FINISHED.value, "finished")

    def mark_as_retrying(self):
        """Marca os metadados como retentativa."""
        self._update_status(VdscStatusEnum.RETRYING.value, "retrying")

    def mark_as_failed(self, error_message: Optional[str] = None):
        """Marca os metadados como falhou."""
        self._update_status(VdscStatusEnum.FAILED.value, f"failed: {error_message}" if error_message else "failed")

    def increment_retry(self) -> bool:
        """Incrementa o contador de tentativas. Retorna True se ainda é possível tentar novamente, False se o máximo foi atingido."""
        if self.retries >= self.max_retry:
            return False
        self.retries += 1
        self.add_log(f"tentativa {self.retries} de {self.max_retry}")
        return True

    def can_retry(self) -> bool:
        """Verifica se ainda é possível realizar nova tentativa."""
        return self.retries < self.max_retry

    def get_duration(self) -> int:
        """Obtém a duração do slice na unidade especificada."""
        return self.end_time - self.start_time

    def get_full_file_name(self) -> str:
        """Obtém o nome completo do arquivo com extensão."""
        return f"{self.file_name}.{self.extension_file}"

    def to_dict(self) -> dict:
        """Converte os metadados para representação em dicionário."""
        return {
            "videoId": self.video_id,
            "fileName": self.file_name,
            "extension_file": self.extension_file,
            "status": self.status,
            "created": self.created.isoformat() + "Z" if self.created else None,
            "userId": self.user_id,
            "totalTime": self.total_time,
            "unitTime": self.unit_time,
            "startTime": self.start_time,
            "endTime": self.end_time,
            "timeInterval": self.time_interval,
            "maxRetry": self.max_retry,
            "retries": self.retries,
            "quality": self.quality,
            "logs": [log.to_dict() if isinstance(log, LogEntry) else log for log in self.logs]
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'VdscMetadata':
        """Cria VideoSliceMetadata a partir de um dicionário."""
        created_str = data['created']
        created = None
        if created_str:
            # Remove sufixo 'Z' se presente
            created_str = created_str.rstrip('Z')
            created = datetime.fromisoformat(created_str)

        logs_data = data.get('logs', [])
        logs = [LogEntry.from_dict(log) for log in logs_data]

        dto = VdscMetadataDTO(
            video_id=data['videoId'],
            file_name=data['fileName'],
            extension=data.get('extension_file', data.get('extension', 'mp4')),
            user_id=data['userId'],
            total_time=data['totalTime'],
            unit_time=data.get('unitTime', 's'),
            start_time=data['startTime'],
            end_time=data['endTime'],
            time_interval=data.get('timeInterval', []),
            max_retry=data.get('maxRetry', 3),
            quality=data.get('quality', VideoQuality.HIGH.value)
        )

        return cls(
            dto=dto,
            status=data.get('status', VdscStatusEnum),
            created=created,
            retries=data.get('retries', 0),
            logs=logs
        )

    def __repr__(self) -> str:
        return (f"VideoSliceMetadata(video_id='{self.video_id}', "
                f"file_name='{self.file_name}', status='{self.status}', "
                f"user_id='{self.user_id}', retries={self.retries}/{self.max_retry})")



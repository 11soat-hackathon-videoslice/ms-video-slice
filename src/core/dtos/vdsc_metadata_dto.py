"""Data Transfer Objects for Video Slice Metadata."""
from dataclasses import dataclass
from typing import List, Dict, Any



@dataclass
class LogEntryDTO:
    """DTO for log entry."""

    timestamp: str
    info: str

    def validate(self) -> bool:

        if not self.timestamp or not isinstance(self.timestamp, str) or self.timestamp.strip() == "":
            raise Exception("O campo 'timestamp' é obrigatório e deve ser uma string não vazia", "timestamp")

        if not self.info or not isinstance(self.info, str) or self.info.strip() == "":
            raise Exception("O campo 'info' é obrigatório e deve ser uma string não vazia", "info")

        return True

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "info": self.info
        }

@dataclass
class VdscMetadataDTO:
    """DTO for video slice metadata response."""

    video_id: str
    file_name: str
    extension_file: str
    status: str
    created: str
    user_id: str
    total_time: int
    unit_time: str
    start_time: int
    end_time: int
    time_interval: List[str]
    max_retry: int
    retries: int
    quality: str
    logs: List[LogEntryDTO]

    def validate(self) -> bool:
        # Validação de campos string obrigatórios
        if not self.video_id or not isinstance(self.video_id, str) or self.video_id.strip() == "":
            raise Exception("O campo 'video_id' é obrigatório e deve ser uma string não vazia", "video_id")

        if not self.file_name or not isinstance(self.file_name, str) or self.file_name.strip() == "":
            raise Exception("O campo 'file_name' é obrigatório e deve ser uma string não vazia", "file_name")

        if not self.extension_file or not isinstance(self.extension_file, str) or self.extension_file.strip() == "":
            raise Exception("O campo 'extension_file' é obrigatório e deve ser uma string não vazia", "extension_file")

        if not self.status or not isinstance(self.status, str) or self.status.strip() == "":
            raise Exception("O campo 'status' é obrigatório e deve ser uma string não vazia", "status")

        if not self.created or not isinstance(self.created, str) or self.created.strip() == "":
            raise Exception("O campo 'created' é obrigatório e deve ser uma string não vazia", "created")

        if not self.user_id or not isinstance(self.user_id, str) or self.user_id.strip() == "":
            raise Exception("O campo 'user_id' é obrigatório e deve ser uma string não vazia", "user_id")

        if not self.unit_time or not isinstance(self.unit_time, str) or self.unit_time.strip() == "":
            raise Exception("O campo 'unit_time' é obrigatório e deve ser uma string não vazia", "unit_time")

        if not self.quality or not isinstance(self.quality, str) or self.quality.strip() == "":
            raise Exception("O campo 'quality' é obrigatório e deve ser uma string não vazia", "quality")

        # Validação de campos numéricos obrigatórios
        if not isinstance(self.total_time, int):
            raise Exception("O campo 'total_time' deve ser um número inteiro", "total_time")

        if self.total_time < 0:
            raise Exception("O campo 'total_time' deve ser um número positivo ou zero", "total_time")

        if not isinstance(self.start_time, int):
            raise Exception("O campo 'start_time' deve ser um número inteiro", "start_time")

        if self.start_time < 0:
            raise Exception("O campo 'start_time' deve ser um número positivo ou zero", "start_time")

        if not isinstance(self.end_time, int):
            raise Exception("O campo 'end_time' deve ser um número inteiro", "end_time")

        if self.end_time < 0:
            raise Exception("O campo 'end_time' deve ser um número positivo ou zero", "end_time")

        if self.start_time > self.end_time:
            raise Exception("O campo 'start_time' não pode ser maior que 'end_time'", "start_time")

        if not isinstance(self.max_retry, int):
            raise Exception("O campo 'max_retry' deve ser um número inteiro", "max_retry")

        if self.max_retry < 0:
            raise Exception("O campo 'max_retry' deve ser um número positivo ou zero", "max_retry")

        if not isinstance(self.retries, int):
            raise Exception("O campo 'retries' deve ser um número inteiro", "retries")

        if self.retries < 0:
            raise Exception("O campo 'retries' deve ser um número positivo ou zero", "retries")

        # Validação de lista obrigatória (time_interval)
        if not isinstance(self.time_interval, list):
            raise Exception("O campo 'time_interval' deve ser uma lista", "time_interval")

        if len(self.time_interval) == 0:
            raise Exception("O campo 'time_interval' não pode ser uma lista vazia", "time_interval")

        for idx, interval in enumerate(self.time_interval):
            if not isinstance(interval, str) or interval.strip() == "":
                raise Exception(f"O item {idx} do 'time_interval' deve ser uma string não vazia", "time_interval")

        # Validação de logs (pode ser vazio)
        if not isinstance(self.logs, list):
            raise Exception("O campo 'logs' deve ser uma lista", "logs")

        # Valida cada log se a lista não estiver vazia
        for idx, log in enumerate(self.logs):
            if not isinstance(log, LogEntryDTO):
                raise Exception(f"O item {idx} do 'logs' deve ser uma instância de LogEntryDTO", "logs")
            try:
                log.validate()
            except Exception as e:
                raise Exception(f"Erro no log {idx}: {e.message}", "logs")

        return True

    def to_dict(self) -> dict:
        """Convert DTO to dictionary."""
        return {
            "videoId": self.video_id,
            "fileName": self.file_name,
            "extension_file": self.extension_file,
            "status": self.status,
            "created": self.created,
            "userId": self.user_id,
            "totalTime": self.total_time,
            "unitTime": self.unit_time,
            "startTime": self.start_time,
            "endTime": self.end_time,
            "timeInterval": self.time_interval,
            "maxRetry": self.max_retry,
            "retries": self.retries,
            "quality": self.quality,
            "logs": [log.to_dict() for log in self.logs]
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'VdscMetadataDTO':
        """Create DTO from dictionary."""
        logs_data = data.get('logs', [])
        logs = [
            LogEntryDTO(timestamp=log['timestamp'], info=log['info'])
            if isinstance(log, dict)
            else log
            for log in logs_data
        ]

        return cls(
            video_id=data['videoId'],
            file_name=data['fileName'],
            extension_file=data['extension_file'],
            status=data['status'],
            created=data['created'],
            user_id=data['userId'],
            total_time=data['totalTime'],
            unit_time=data['unitTime'],
            start_time=data['startTime'],
            end_time=data['endTime'],
            time_interval=data['timeInterval'],
            max_retry=data['maxRetry'],
            retries=data['retries'],
            quality=data['quality'],
            logs=logs
        )

    @classmethod
    def from_dynamodb_item(cls, item: Dict[str, Any]) -> 'VdscMetadataDTO':
        """Create DTO from DynamoDB item."""
        logs_list = item.get('logs', {}).get('L', [])
        logs = [
            LogEntryDTO(
                timestamp=log_item['M']['timestamp']['S'],
                info=log_item['M']['info']['S']
            )
            for log_item in logs_list
        ]

        return cls(
            video_id=item['videoId']['S'],
            file_name=item['fileName']['S'],
            extension_file=item['extensionFile']['S'],
            status=item['status']['S'],
            created=item['created']['S'],
            user_id=item['userId']['S'],
            total_time=int(item['totalTime']['N']),
            unit_time=item['unitTime']['S'],
            start_time=int(item['startTime']['N']),
            end_time=int(item['endTime']['N']),
            time_interval=[interval['S'] for interval in item['timeInterval']['L']],
            max_retry=int(item['maxRetry']['N']),
            retries=int(item['retries']['N']),
            quality=item['quality']['S'],
            logs=logs
        )

    def to_dynamodb_item(self) -> Dict[str, Any]:
        """Converte DTO para formato DynamoDB"""
        logs_dynamodb = {
            'L': [
                {
                    'M': {
                        'timestamp': {'S': log.timestamp},
                        'info': {'S': log.info}
                    }
                }
                for log in self.logs
            ]
        }

        return {
            'videoId': {'S': str(self.video_id)},
            'fileName': {'S': self.file_name},
            'extensionFile': {'S': self.extension_file},
            'status': {'S': self.status},
            'created': {'S': self.created},
            'userId': {'S': self.user_id},
            'totalTime': {'N': str(self.total_time)},
            'unitTime': {'S': self.unit_time},
            'startTime': {'N': str(self.start_time)},
            'endTime': {'N': str(self.end_time)},
            'timeInterval': {'L': [{'S': interval} for interval in self.time_interval]},
            'maxRetry': {'N': str(self.max_retry)},
            'retries': {'N': str(self.retries)},
            'quality': {'S': self.quality},
            'logs': logs_dynamodb
        }



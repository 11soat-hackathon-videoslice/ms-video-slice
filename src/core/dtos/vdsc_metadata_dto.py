"""Data Transfer Objects for Video Slice Metadata."""
from dataclasses import dataclass
from typing import List, Dict, Any



@dataclass
class LogEntryDTO:
    """DTO for log entry."""

    timestamp: str
    info: str

    def _validate_required_string(self, value: str, field_name: str) -> None:
        """Valida campo string obrigatório"""
        if not value or not isinstance(value, str) or value.strip() == "":
            raise ValueError(f"O campo '{field_name}' é obrigatório e deve ser uma string não vazia")

    def validate(self) -> bool:
        """Valida campos obrigatórios do LogEntry"""
        self._validate_required_string(self.timestamp, "timestamp")
        self._validate_required_string(self.info, "info")
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

    def _validate_required_string(self, value: str, field_name: str) -> None:
        """Valida campo string obrigatório"""
        if not value or not isinstance(value, str) or value.strip() == "":
            raise ValueError(f"O campo '{field_name}' é obrigatório e deve ser uma string não vazia")

    def _validate_non_negative_integer(self, value: int, field_name: str) -> None:
        """Valida campo inteiro não negativo"""
        if not isinstance(value, int):
            raise ValueError(f"O campo '{field_name}' deve ser um número inteiro")
        if value < 0:
            raise ValueError(f"O campo '{field_name}' deve ser um número positivo ou zero")

    def _validate_string_fields(self) -> None:
        """Valida todos os campos string obrigatórios"""
        self._validate_required_string(self.video_id, "video_id")
        self._validate_required_string(self.file_name, "file_name")
        self._validate_required_string(self.extension_file, "extension_file")
        self._validate_required_string(self.status, "status")
        self._validate_required_string(self.created, "created")
        self._validate_required_string(self.user_id, "user_id")
        self._validate_required_string(self.unit_time, "unit_time")
        self._validate_required_string(self.quality, "quality")

    def _validate_numeric_fields(self) -> None:
        """Valida todos os campos numéricos"""
        self._validate_non_negative_integer(self.total_time, "total_time")
        self._validate_non_negative_integer(self.start_time, "start_time")
        self._validate_non_negative_integer(self.end_time, "end_time")
        self._validate_non_negative_integer(self.max_retry, "max_retry")
        self._validate_non_negative_integer(self.retries, "retries")

    def _validate_time_range(self) -> None:
        """Valida intervalo de tempo"""
        if self.start_time > self.end_time:
            raise ValueError("O campo 'start_time' não pode ser maior que 'end_time'")

    def _validate_time_interval_list(self) -> None:
        """Valida lista de intervalos de tempo"""
        if not isinstance(self.time_interval, list):
            raise ValueError("O campo 'time_interval' deve ser uma lista")
        if len(self.time_interval) == 0:
            raise ValueError("O campo 'time_interval' não pode ser uma lista vazia")
        for idx, interval in enumerate(self.time_interval):
            if not isinstance(interval, str) or interval.strip() == "":
                raise ValueError(f"O item {idx} do 'time_interval' deve ser uma string não vazia")

    def _validate_logs_list(self) -> None:
        """Valida lista de logs"""
        if not isinstance(self.logs, list):
            raise ValueError("O campo 'logs' deve ser uma lista")
        for idx, log in enumerate(self.logs):
            if not isinstance(log, LogEntryDTO):
                raise ValueError(f"O item {idx} do 'logs' deve ser uma instância de LogEntryDTO")
            try:
                log.validate()
            except Exception as e:
                raise ValueError(f"Erro no log {idx}: {e.args[0] if e.args else str(e)}")

    def validate(self) -> bool:
        """Valida todos os campos do DTO"""
        self._validate_string_fields()
        self._validate_numeric_fields()
        self._validate_time_range()
        self._validate_time_interval_list()
        self._validate_logs_list()
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



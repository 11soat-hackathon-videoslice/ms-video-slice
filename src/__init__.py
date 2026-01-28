# Handler Lambda
from .aws.handler.vdsc_exception_handler import VdscExceptionHandler

# Configurações
from .aws.config.vdsc_config import VdscConfig

# DataProxy
from .aws.dataproxy.vdsc_dataproxy import VdscDataProxy

# Repositórios
from .aws.datasources.database.dynamodb_repository import DynamoDBRepository
from .aws.datasources.storage.s3_repository import S3StorageRepository
from .aws.datasources.producer.event_producer import EventProducer

# Core - Adapters e Use Cases
from .core.adapters import VdscController
from .core.applications import VdscProcessUseCase

# Core - Domain e DTOs
from .core.domain import LogEntry, VdscMetadata
from .core.dtos import EventDTO, LogEntryDTO, VdscMetadataDTO

# Core - Enums
from .core.enums import VdscStatusEnum, VideoQuality

# Core - Exceptions
from .core.exceptions import VdscException

# Core - Interfaces
from .core.interfaces import VdscControllerInterface, VdscDataProxyInterface, VdscGatewayInferface

__all__ = [
    # Handler Lambda
    'VdscExceptionHandler',

    # Configurações
    'VdscConfig',

    # DataProxy
    'VdscDataProxy',

    # Repositórios
    'DynamoDBRepository',
    'S3StorageRepository',
    'EventProducer',

    # Core - Adapters e Use Cases
    'VdscController',
    'VdscProcessUseCase',

    # Core - Domain e DTOs
    'LogEntry',
    'VdscMetadata',
    'EventDTO',
    'LogEntryDTO',
    'VdscMetadataDTO',

    # Core - Enums
    'VdscStatusEnum',
    'VideoQuality',

    # Core - Exceptions
    'VdscException',

    # Core - Interfaces
    'VdscControllerInterface',
    'VdscDataProxyInterface',
    'VdscGatewayInferface',
]

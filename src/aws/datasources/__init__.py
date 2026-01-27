"""
DataSources package - Database, Storage e Event Producer
"""

from .database import DynamoDBInterface, DynamoDBRepository
from .storage import S3Interface, S3StorageRepository

try:
    from .producer.event_producer import EventProducer
    from .producer.event_producer_interface import EventProducerInterface
    _producer_available = True
except ImportError as e:
    print(f"Warning: Could not import EventProducer: {e}")
    EventProducer = None
    EventProducerInterface = None
    _producer_available = False

__all__ = [
    'DynamoDBInterface',
    'DynamoDBRepository',
    'S3Interface',
    'S3StorageRepository',
]

if _producer_available:
    __all__.extend(['EventProducer', 'EventProducerInterface'])


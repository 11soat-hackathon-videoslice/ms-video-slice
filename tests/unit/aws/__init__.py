"""Pacote de testes unitários"""
from . import config
from . import dataproxy
from . import datasources
from . import handler

from .config import (TestVdscConfig, test_vdsc_config,)
from .dataproxy import (TestDictToDynamoDBFormat, TestVdscDataProxy,
                        test_vdsc_dataproxy,)
from .datasources import (TestDynamoDBRepository, TestEventProducer,
                          TestS3StorageRepository, database, producer, storage,
                          test_dynamodb_repository, test_event_producer,
                          test_s3_repository,)
from .handler import (TestVdscExceptionHandler, test_vdsc_exception_handler,)

__all__ = ['TestDictToDynamoDBFormat', 'TestDynamoDBRepository',
           'TestEventProducer', 'TestS3StorageRepository', 'TestVdscConfig',
           'TestVdscDataProxy', 'TestVdscExceptionHandler', 'config',
           'database', 'dataproxy', 'datasources', 'handler', 'producer',
           'storage', 'test_dynamodb_repository', 'test_event_producer',
           'test_s3_repository', 'test_vdsc_config', 'test_vdsc_dataproxy',
           'test_vdsc_exception_handler']

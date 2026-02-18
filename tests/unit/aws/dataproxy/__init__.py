"""Pacote de testes unitários para dataproxy"""
from . import test_vdsc_dataproxy

from .test_vdsc_dataproxy import (TestDictToDynamoDBFormat, TestVdscDataProxy,)

__all__ = ['TestDictToDynamoDBFormat', 'TestVdscDataProxy',
           'test_vdsc_dataproxy']

"""Testes unitários para VdscConfig"""
import pytest
import os
from unittest.mock import patch
from aws.config.slice_config import SliceVdscConfig


@pytest.mark.unit
class TestVdscConfig:
    """Testes para a classe de configuração"""

    def test_singleton_pattern(self):
        """Testa se VdscConfig implementa o padrão Singleton"""
        config1 = SliceVdscConfig()
        config2 = SliceVdscConfig()
        assert config1 is config2

    def test_default_aws_config(self):
        """Testa configurações padrão da AWS"""
        config = SliceVdscConfig()
        assert config.aws['aws_region'] == 'us-east-1'

    def test_default_s3_config(self):
        """Testa configurações padrão do S3"""
        config = SliceVdscConfig()
        assert config.s3_bucket['bucket_name'] == os.getenv('S3_BUCKET_NAME', 'vdsc-prd-s3-videos')
        assert config.vdsc['dir_uploads'] == 'uploads'
        assert config.vdsc['dir_finished'] == 'finished'
        assert config.vdsc['dir_tmp'] == '/tmp'

    def test_default_eventbus_config(self):
        """Testa configurações padrão do EventBus"""
        config = SliceVdscConfig()
        assert config.eventbus['name'] == os.getenv('EVENT_BUS_NAME', 'vdsc-prd-event-bus')

    def test_default_dynamodb_config(self):
        """Testa configurações padrão do DynamoDB"""
        config = SliceVdscConfig()
        assert config.dynamodb['table_name'] == os.getenv('DYNAMODB_TABLE_NAME', 'VideoSlice')

    def test_default_vdsc_config(self):
        """Testa configurações padrão de processamento de vídeo"""
        config = SliceVdscConfig()
        assert config.vdsc['png_compression_level'] == 9
        assert config.vdsc['zip_compression_level'] == 5
        assert config.vdsc['quality']['ultra'] == 1080
        assert config.vdsc['quality']['high'] == 720
        assert config.vdsc['quality']['medium'] == 480
        assert config.vdsc['quality']['low'] == 360

    @patch.dict(os.environ, {
        'AWS_REGION': 'us-west-2',
        'S3_BUCKET_NAME': 'test-bucket',
        'DYNAMODB_TABLE_NAME': 'TestTable'
    })
    def test_environment_variables_override(self):
        """Testa se variáveis de ambiente sobrescrevem valores padrão"""
        # Reset singleton para testar com novas variáveis de ambiente
        SliceVdscConfig._instance = None
        config = SliceVdscConfig()
        assert config.aws['aws_region'] == 'us-west-2'
        assert config.s3_bucket['bucket_name'] == 'test-bucket'
        assert config.dynamodb['table_name'] == 'TestTable'
        # Reset singleton após o teste
        SliceVdscConfig._instance = None


"""Testes unitários para VdscConfig"""
import pytest
import os
from unittest.mock import patch
from src.aws.config.vdsc_config import VdscConfig


@pytest.mark.unit
class TestVdscConfig:
    """Testes para a classe de configuração"""

    def test_singleton_pattern(self):
        """Testa se VdscConfig implementa o padrão Singleton"""
        config1 = VdscConfig()
        config2 = VdscConfig()
        assert config1 is config2

    def test_default_aws_config(self):
        """Testa configurações padrão da AWS"""
        config = VdscConfig()
        assert config.aws['region'] == 'us-east-1'
        assert 'account_id' in config.aws

    def test_default_s3_config(self):
        """Testa configurações padrão do S3"""
        config = VdscConfig()
        assert config.s3_bucket['name'] == 'vdsc-prd-s3-videos'
        assert config.s3_bucket['dir_uploads'] == 'uploads/'
        assert config.s3_bucket['dir_finished'] == 'finished/'
        assert config.s3_bucket['dir_processing'] == 'processing/'

    def test_default_sqs_config(self):
        """Testa configurações padrão do SQS"""
        config = VdscConfig()
        assert 'url' in config.sqs
        assert 'dlq_name' in config.sqs

    def test_default_eventbus_config(self):
        """Testa configurações padrão do EventBus"""
        config = VdscConfig()
        assert config.eventbus['name'] == 'vdsc-prd-event-bus'

    def test_default_dynamodb_config(self):
        """Testa configurações padrão do DynamoDB"""
        config = VdscConfig()
        assert config.dynamodb['table_name'] == 'VideoSlice'

    def test_default_vdsc_config(self):
        """Testa configurações padrão de processamento de vídeo"""
        config = VdscConfig()
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
        VdscConfig._instance = None
        config = VdscConfig()
        assert config.aws['region'] == 'us-west-2'
        assert config.s3_bucket['name'] == 'test-bucket'
        assert config.dynamodb['table_name'] == 'TestTable'
        # Reset singleton após o teste
        VdscConfig._instance = None

    def test_parse_quality_json_format(self):
        """Testa parsing de quality com formato JSON"""
        VdscConfig._instance = None
        config = VdscConfig()
        quality_json = '{"ultra": 1080, "high": 720, "medium": 480, "low": 360}'
        result = config._parse_quality(quality_json)
        assert isinstance(result, dict)
        assert result['ultra'] == 1080
        assert result['high'] == 720

    def test_parse_quality_python_format(self):
        """Testa parsing de quality com formato Python"""
        VdscConfig._instance = None
        config = VdscConfig()
        quality_python = "{'ultra': 1080, 'high': 720, 'medium': 480, 'low': 360}"
        result = config._parse_quality(quality_python)
        assert isinstance(result, dict)
        assert result['ultra'] == 1080
        assert result['high'] == 720

    def test_parse_quality_invalid_string(self):
        """Testa parsing de quality com string inválida retorna padrão"""
        VdscConfig._instance = None
        config = VdscConfig()
        quality_invalid = "invalid string"
        result = config._parse_quality(quality_invalid)
        assert isinstance(result, dict)
        assert result['ultra'] == 1080
        assert result['high'] == 720
        assert result['medium'] == 480
        assert result['low'] == 360


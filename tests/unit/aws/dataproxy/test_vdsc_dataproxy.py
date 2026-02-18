"""Testes unitários para VdscDataProxy"""
import pytest
from unittest.mock import Mock
from src.aws.dataproxy.slice_dataproxy import SliceDataProxy, dict_to_dynamodb_format
from core.dtos.vdsc_metadata_dto import VdscMetadataDTO
from core.dtos.notification_dto import NotificationDto


@pytest.mark.unit
class TestVdscDataProxy:
    """Testes para o DataProxy"""

    @pytest.fixture
    def mock_dynamodb(self):
        """Mock para DynamoDB"""
        return Mock()

    @pytest.fixture
    def mock_s3(self):
        """Mock para S3"""
        return Mock()

    @pytest.fixture
    def mock_event_producer(self):
        """Mock para Event Producer"""
        return Mock()

    @pytest.fixture
    def mock_cloudwatch(self):
        """Mock para CloudWatch"""
        return Mock()

    @pytest.fixture
    def dataproxy(self, mock_dynamodb, mock_s3, mock_event_producer, mock_cloudwatch):
        """Fixture para criar instância do DataProxy"""
        return SliceDataProxy(
            dynamodb=mock_dynamodb,
            storage=mock_s3,
            event_producer=mock_event_producer,
            cloudwatch=mock_cloudwatch
        )

    def test_delete_file(self, dataproxy, mock_s3):
        """Testa deleção de arquivo"""
        dataproxy.delete_file("test/file.txt")
        mock_s3.delete_file.assert_called_once_with("test/file.txt")

    def test_open_file(self, dataproxy, mock_s3):
        """Testa abertura de arquivo"""
        mock_s3.open_file.return_value = b"file content"
        result = dataproxy.open_file("test/file.txt")
        assert result == b"file content"
        mock_s3.open_file.assert_called_once_with("test/file.txt")

    def test_save_file(self, dataproxy, mock_s3):
        """Testa salvamento de arquivo"""
        dataproxy.save_file("test/file.txt", b"content")
        mock_s3.save_file.assert_called_once_with("test/file.txt", b"content")

    def test_send_event(self, dataproxy, mock_event_producer):
        """Testa envio de evento de retry agendado"""
        from datetime import datetime
        mock_metadata = Mock()
        mock_metadata.to_dynamodb_item.return_value = {"videoId": "test"}
        schedule_time = datetime(2026, 1, 13, 0, 0, 0)
        schedule_config = {"retry_arn": "arn:test"}
        dataproxy.send_schedule_retry_event(mock_metadata, schedule_time, schedule_config)
        mock_event_producer.send_schedule_retry_event.assert_called_once_with(
            {"videoId": "test"}, schedule_time, schedule_config
        )

    def test_send_schedule_retry_event_with_metadata_conversion(self, dataproxy, mock_event_producer):
        """Testa envio de evento de retry com conversão de metadados para formato DynamoDB"""
        from datetime import datetime
        mock_metadata = Mock(spec=VdscMetadataDTO)
        mock_metadata.to_dynamodb_item.return_value = {
            "videoId": {"S": "video123"},
            "status": {"S": "retrying"},
            "retries": {"N": "1"}
        }
        schedule_time = datetime(2026, 1, 13, 10, 30, 0)
        schedule_config = {
            "retry_arn": "arn:aws:sqs:us-east-1:123456789012:queue",
            "retry_role_arn": "arn:aws:iam::123456789012:role/scheduler-role",
            "retry_dlq": "arn:aws:sqs:us-east-1:123456789012:dlq",
            "retry_backoff_factor": 10
        }

        dataproxy.send_schedule_retry_event(mock_metadata, schedule_time, schedule_config)

        mock_event_producer.send_schedule_retry_event.assert_called_once_with(
            mock_metadata.to_dynamodb_item.return_value,
            schedule_time,
            schedule_config
        )
        mock_metadata.to_dynamodb_item.assert_called_once()

    def test_send_schedule_retry_event_preserves_schedule_config(self, dataproxy, mock_event_producer):
        """Testa se send_schedule_retry_event preserva as configurações de agendamento"""
        from datetime import datetime
        mock_metadata = Mock(spec=VdscMetadataDTO)
        mock_metadata.to_dynamodb_item.return_value = {"videoId": {"S": "vid456"}}
        schedule_time = datetime(2026, 1, 15, 14, 45, 30)
        schedule_config = {
            "retry_arn": "arn:aws:sqs:us-east-1:123456789012:retry-queue",
            "retry_role_arn": "arn:aws:iam::123456789012:role/scheduler",
            "retry_dlq": "arn:aws:sqs:us-east-1:123456789012:retry-dlq",
            "retry_backoff_factor": 5
        }

        dataproxy.send_schedule_retry_event(mock_metadata, schedule_time, schedule_config)

        call_args = mock_event_producer.send_schedule_retry_event.call_args
        assert call_args[0][1] == schedule_time
        assert call_args[0][2] == schedule_config
        assert call_args[0][2]["retry_backoff_factor"] == 5

    def test_update_metadata_by_video_id(self, dataproxy, mock_dynamodb):
        """Testa atualização de metadados"""
        mock_dto = Mock(spec=VdscMetadataDTO)
        mock_dynamodb.update_metadata_by_video_id.return_value = mock_dto

        result = dataproxy.update_metadata_by_video_id(mock_dto)

        assert result == mock_dto
        mock_dynamodb.update_metadata_by_video_id.assert_called_once_with(mock_dto)

    def test_send_notification(self, dataproxy, mock_event_producer):
        """Testa envio de notificação"""
        mock_notification = Mock(spec=NotificationDto)

        dataproxy.send_notification(mock_notification)

        mock_event_producer.send_notification.assert_called_once_with(mock_notification)

    def test_send_notification_delegates_to_event_producer(self, dataproxy, mock_event_producer):
        """Testa que send_notification delega corretamente para event_producer"""
        mock_notification = Mock(spec=NotificationDto)
        dataproxy.send_notification(mock_notification)
        mock_event_producer.send_notification.assert_called_once_with(mock_notification)

    def test_upload_finished_zip(self, dataproxy, mock_s3):
        """Testa upload de zip finalizado"""
        dataproxy.upload_finished_zip("output/dir", "target/path.zip")
        mock_s3.upload_finished_zip.assert_called_once_with("output/dir", "target/path.zip")

    def test_delete_temp_files(self, dataproxy, mock_s3):
        """Testa deleção de arquivos temporários"""
        dataproxy.delete_temp_files("tmp/path")
        mock_s3.delete_temp_files.assert_called_once_with("tmp/path")

    def test_send_metric(self, dataproxy, mock_cloudwatch):
        """Testa envio de métrica"""
        metric_info = {
            'resize': True,
            'original_min_size': 1080,
            'resize_output': 720,
            'quality_output_level': 'high',
            'frames_processed': 10,
            'workers': 4,
            'video_size_mb': 100.0,
            'process_total_time_seconds': 15.5,
            'efficiency_per_frame_seconds': 1.55
        }

        dataproxy.send_metric(metric_info)

        mock_cloudwatch.send_metric.assert_called_once_with(metric_info)

    def test_send_metric_without_resize(self, dataproxy, mock_cloudwatch):
        """Testa envio de métrica sem redimensionamento"""
        metric_info = {
            'resize': False,
            'original_min_size': 720,
            'resize_output': 720,
            'quality_output_level': 'original',
            'frames_processed': 5,
            'workers': 2,
            'video_size_mb': 50.0,
            'process_total_time_seconds': 8.0,
            'efficiency_per_frame_seconds': 1.6
        }

        dataproxy.send_metric(metric_info)

        mock_cloudwatch.send_metric.assert_called_once_with(metric_info)

    def test_send_metric_with_different_resolutions(self, dataproxy, mock_cloudwatch):
        """Testa envio de métricas com diferentes resoluções"""
        resolutions = [
            (1080, 720),  # Ultra -> High
            (720, 480),   # High -> Medium
            (480, 360),   # Medium -> Low
        ]

        for original, output in resolutions:
            metric_info = {
                'resize': True,
                'original_min_size': original,
                'resize_output': output,
                'quality_output_level': 'medium',
                'frames_processed': 3,
                'workers': 2,
                'video_size_mb': 25.0,
                'process_total_time_seconds': 5.0,
                'efficiency_per_frame_seconds': 1.67
            }

            dataproxy.send_metric(metric_info)

        assert mock_cloudwatch.send_metric.call_count == len(resolutions)

    def test_send_metric_with_high_performance(self, dataproxy, mock_cloudwatch):
        """Testa envio de métrica com alto desempenho (muitos workers)"""
        metric_info = {
            'resize': True,
            'original_min_size': 1080,
            'resize_output': 480,
            'quality_output_level': 'medium',
            'frames_processed': 100,
            'workers': 16,
            'video_size_mb': 500.0,
            'process_total_time_seconds': 60.0,
            'efficiency_per_frame_seconds': 0.6
        }

        dataproxy.send_metric(metric_info)

        mock_cloudwatch.send_metric.assert_called_once_with(metric_info)
        args = mock_cloudwatch.send_metric.call_args[0]
        assert args[0]['workers'] == 16
        assert args[0]['efficiency_per_frame_seconds'] < 1.0

    def test_send_metric_preserves_all_fields(self, dataproxy, mock_cloudwatch):
        """Testa que send_metric preserva todos os campos da métrica"""
        metric_info = {
            'resize': True,
            'original_min_size': 1080,
            'resize_output': 720,
            'quality_output_level': 'high',
            'frames_processed': 10,
            'workers': 4,
            'video_size_mb': 100.0,
            'process_total_time_seconds': 15.5,
            'efficiency_per_frame_seconds': 1.55
        }

        dataproxy.send_metric(metric_info)

        args = mock_cloudwatch.send_metric.call_args[0]
        assert args[0]['resize'] == metric_info['resize']
        assert args[0]['original_min_size'] == metric_info['original_min_size']
        assert args[0]['resize_output'] == metric_info['resize_output']
        assert args[0]['quality_output_level'] == metric_info['quality_output_level']
        assert args[0]['frames_processed'] == metric_info['frames_processed']
        assert args[0]['workers'] == metric_info['workers']
        assert args[0]['video_size_mb'] == metric_info['video_size_mb']
        assert args[0]['process_total_time_seconds'] == metric_info['process_total_time_seconds']
        assert args[0]['efficiency_per_frame_seconds'] == metric_info['efficiency_per_frame_seconds']

@pytest.mark.unit
class TestDictToDynamoDBFormat:
    """Testes para função de conversão dict_to_dynamodb_format"""

    def test_convert_string(self):
        """Testa conversão de string"""
        result = dict_to_dynamodb_format({"name": "test"})
        assert result == {"name": {"S": "test"}}

    def test_convert_int(self):
        """Testa conversão de inteiro"""
        result = dict_to_dynamodb_format({"age": 25})
        assert result == {"age": {"N": "25"}}

    def test_convert_float(self):
        """Testa conversão de float"""
        result = dict_to_dynamodb_format({"price": 19.99})
        assert result == {"price": {"N": "19.99"}}

    def test_convert_bool(self):
        """Testa conversão de booleano"""
        result = dict_to_dynamodb_format({"active": True})
        assert result == {"active": {"BOOL": True}}

    def test_convert_none(self):
        """Testa conversão de None"""
        result = dict_to_dynamodb_format({"value": None})
        assert result == {"value": {"NULL": True}}

    def test_convert_nested_dict(self):
        """Testa conversão de dicionário aninhado"""
        result = dict_to_dynamodb_format({"user": {"name": "test", "age": 25}})
        assert result["user"]["M"]["name"]["S"] == "test"
        assert result["user"]["M"]["age"]["N"] == "25"

    def test_convert_list(self):
        """Testa conversão de lista"""
        result = dict_to_dynamodb_format({"tags": ["tag1", "tag2"]})
        assert "L" in result["tags"]
        assert len(result["tags"]["L"]) == 2

    def test_convert_empty_dict(self):
        """Testa conversão de dicionário vazio"""
        result = dict_to_dynamodb_format({})
        assert result == {}

    def test_convert_complex_structure(self):
        """Testa conversão de estrutura complexa"""
        data = {
            'id': 'video123',
            'count': 10,
            'price': 29.99,
            'active': True,
            'tags': ['tag1', 'tag2'],
            'metadata': {
                'title': 'Test Video',
                'duration': 3600
            },
            'optional': None
        }

        result = dict_to_dynamodb_format(data)

        assert result['id'] == {'S': 'video123'}
        assert result['count'] == {'N': '10'}
        assert result['price'] == {'N': '29.99'}
        assert result['active'] == {'BOOL': True}
        assert 'L' in result['tags']
        assert 'M' in result['metadata']
        assert result['optional'] == {'NULL': True}

    def test_convert_nested_lists(self):
        """Testa conversão de listas aninhadas"""
        data = {'matrix': [['a', 'b'], ['c', 'd']]}
        result = dict_to_dynamodb_format(data)

        assert 'matrix' in result
        assert 'L' in result['matrix']

    def test_convert_list_with_mixed_types(self):
        """Testa conversão de lista com tipos mistos"""
        data = {'mixed': ['string', 123, True, None]}
        result = dict_to_dynamodb_format(data)

        assert 'mixed' in result
        assert 'L' in result['mixed']
        assert len(result['mixed']['L']) == 4

    def test_convert_boolean_false(self):
        """Testa conversão de boolean False"""
        result = dict_to_dynamodb_format({'inactive': False})
        assert result == {'inactive': {'BOOL': False}}

    def test_convert_zero_integer(self):
        """Testa conversão de inteiro zero"""
        result = dict_to_dynamodb_format({'count': 0})
        assert result == {'count': {'N': '0'}}

    def test_convert_negative_number(self):
        """Testa conversão de número negativo"""
        result = dict_to_dynamodb_format({'temperature': -10})
        assert result == {'temperature': {'N': '-10'}}

    def test_convert_deeply_nested_dict(self):
        """Testa conversão de dicionário profundamente aninhado"""
        data = {
            'level1': {
                'level2': {
                    'level3': {
                        'value': 'deep'
                    }
                }
            }
        }
        result = dict_to_dynamodb_format(data)

        assert 'M' in result['level1']
        assert 'M' in result['level1']['M']['level2']
        assert 'M' in result['level1']['M']['level2']['M']['level3']

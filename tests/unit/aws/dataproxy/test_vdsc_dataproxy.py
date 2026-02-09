"""Testes unitários para VdscDataProxy"""
import pytest
from unittest.mock import Mock, patch
from src.aws.dataproxy.vdsc_dataproxy import VdscDataProxy, dict_to_dynamodb_format
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
    def dataproxy(self, mock_dynamodb, mock_s3, mock_event_producer):
        """Fixture para criar instância do DataProxy"""
        return VdscDataProxy(
            dynamodb=mock_dynamodb,
            s3=mock_s3,
            event_producer=mock_event_producer
        )

    def test_create_directory(self, dataproxy, mock_s3):
        """Testa criação de diretório"""
        dataproxy.create_directory("test/path/")
        mock_s3.create_directory.assert_called_once_with("test/path/")

    def test_delete_file(self, dataproxy, mock_s3):
        """Testa deleção de arquivo"""
        dataproxy.delete_file("test/file.txt")
        mock_s3.delete_file.assert_called_once_with("test/file.txt")

    def test_delete_files_by_directory(self, dataproxy, mock_s3):
        """Testa deleção de arquivos por diretório"""
        dataproxy.delete_files_by_directory("test/dir/")
        mock_s3.delete_files_by_directory.assert_called_once_with("test/dir/")

    def test_get_list_paths_by_directory(self, dataproxy, mock_s3):
        """Testa obtenção de lista de caminhos por diretório"""
        mock_s3.get_list_paths_by_directory.return_value = ["file1.txt", "file2.txt"]
        result = dataproxy.get_list_paths_by_directory("test/dir/")
        assert result == ["file1.txt", "file2.txt"]
        mock_s3.get_list_paths_by_directory.assert_called_once_with("test/dir/")

    def test_open_file(self, dataproxy, mock_s3):
        """Testa abertura de arquivo"""
        mock_s3.open_file.return_value = b"file content"
        result = dataproxy.open_file("test/file.txt")
        assert result == b"file content"
        mock_s3.open_file.assert_called_once_with("test/file.txt")

    def test_move_file(self, dataproxy, mock_s3):
        """Testa movimentação de arquivo"""
        dataproxy.move_file("source.txt", "destination.txt")
        mock_s3.move_file.assert_called_once_with("source.txt", "destination.txt")

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

    @patch('threading.Thread')
    def test_send_notification(self, mock_thread_class, dataproxy, mock_event_producer):
        """Testa envio de notificação com threading"""
        mock_notification = Mock(spec=NotificationDto)
        mock_thread_instance = Mock()
        mock_thread_class.return_value = mock_thread_instance

        dataproxy.send_notification(mock_notification)

        mock_thread_class.assert_called_once_with(
            target=mock_event_producer.send_notification,
            args=(mock_notification,),
            daemon=True
        )
        mock_thread_instance.start.assert_called_once()

    @patch('threading.Thread')
    def test_send_notification_delegates_to_event_producer(self, mock_thread_class, dataproxy, mock_event_producer):
        """Testa que send_notification delega corretamente para event_producer em uma thread"""
        mock_notification = Mock(spec=NotificationDto)
        mock_thread_instance = Mock()
        mock_thread_class.return_value = mock_thread_instance

        dataproxy.send_notification(mock_notification)

        mock_thread_class.assert_called_once_with(
            target=mock_event_producer.send_notification,
            args=(mock_notification,),
            daemon=True
        )
        mock_thread_instance.start.assert_called_once()



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

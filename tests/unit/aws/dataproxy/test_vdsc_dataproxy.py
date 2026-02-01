"""Testes unitários para VdscDataProxy"""
import pytest
from unittest.mock import Mock
from src.aws.dataproxy.vdsc_dataproxy import VdscDataProxy, dict_to_dynamodb_format
from src.core.dtos.vdsc_metadata_dto import VdscMetadataDTO


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
        """Testa envio de evento"""
        event_data = {"event": "test"}
        dataproxy.send_event(event_data)
        mock_event_producer.send_event.assert_called_once_with(event_data)

    def test_update_metadata_by_video_id(self, dataproxy, mock_dynamodb):
        """Testa atualização de metadados"""
        mock_dto = Mock(spec=VdscMetadataDTO)
        mock_dynamodb.update_metadata_by_video_id.return_value = mock_dto

        result = dataproxy.update_metadata_by_video_id(mock_dto)

        assert result == mock_dto
        mock_dynamodb.update_metadata_by_video_id.assert_called_once_with(mock_dto)


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


"""Testes unitários para DynamoDBRepository"""
import pytest
from unittest.mock import Mock, patch
from src.aws.datasources.database.dynamodb_repository import DynamoDBRepository
from core.dtos.vdsc_metadata_dto import VdscMetadataDTO


@pytest.mark.unit
class TestDynamoDBRepository:
    """Testes para o repositório DynamoDB"""

    @pytest.fixture
    def mock_dynamodb_client(self):
        """Mock para cliente DynamoDB"""
        return Mock()

    @pytest.fixture
    def repository(self, mock_dynamodb_client):
        """Fixture para criar instância do repositório"""
        with patch('boto3.client', return_value=mock_dynamodb_client):
            repo = DynamoDBRepository(table_name="VideoSlice", region="us-east-1")
            repo.dynamodb_client = mock_dynamodb_client
            return repo

    def test_init(self):
        """Testa inicialização do repositório"""
        with patch('boto3.client') as mock_boto:
            repo = DynamoDBRepository(table_name="TestTable", region="us-west-2")
            assert repo.table_name == "TestTable"
            mock_boto.assert_called_once_with('dynamodb', region_name='us-west-2')

    def test_get_metadata_by_video_id_success(self, repository, mock_dynamodb_client):
        """Testa obtenção de metadados com sucesso"""
        mock_response = {
            'Item': {
                'videoId': {'S': 'video123'},
                'fileName': {'S': 'test.mp4'},
                'extensionFile': {'S': 'mp4'},
                'status': {'S': 'uploaded'},
                'created': {'S': '2026-01-13T00:00:00Z'},
                'userId': {'S': 'user123'},
                'totalTime': {'N': '3600'},
                'unitTime': {'S': 's'},
                'startTime': {'N': '0'},
                'endTime': {'N': '60'},
                'timeInterval': {'L': [{'S': '00:00:00'}]},
                'maxRetry': {'N': '3'},
                'retries': {'N': '0'},
                'quality': {'S': 'high'},
                'logs': {'L': []}
            }
        }
        mock_dynamodb_client.get_item.return_value = mock_response

        result = repository.get_metadata_by_video_id("video123")

        assert result.__class__.__name__ == 'VdscMetadataDTO'
        assert result.video_id == 'video123'
        assert result.file_name == 'test.mp4'
        mock_dynamodb_client.get_item.assert_called_once()

    def test_get_metadata_by_video_id_not_found(self, repository, mock_dynamodb_client):
        """Testa obtenção de metadados quando vídeo não é encontrado"""
        mock_dynamodb_client.get_item.return_value = {}

        with pytest.raises(ValueError, match="não encontrado"):
            repository.get_metadata_by_video_id("nonexistent")

    def test_get_metadata_by_video_id_error(self, repository, mock_dynamodb_client):
        """Testa erro ao obter metadados"""
        mock_dynamodb_client.get_item.side_effect = Exception("DynamoDB error")

        with pytest.raises(Exception):
            repository.get_metadata_by_video_id("video123")

    def test_extract_video_id_success(self, repository):
        """Testa extração de videoId com sucesso"""
        update_data = {'videoId': {'S': 'video123'}}
        result = repository._extract_video_id(update_data)
        assert result == 'video123'

    def test_extract_video_id_missing(self, repository):
        """Testa extração de videoId quando campo está ausente"""
        with pytest.raises(ValueError, match="obrigatório"):
            repository._extract_video_id({})

    def test_extract_video_id_invalid_format(self, repository):
        """Testa extração de videoId com formato inválido"""
        update_data = {'videoId': {'N': '123'}}
        with pytest.raises(ValueError, match="formato"):
            repository._extract_video_id(update_data)

    def test_filter_fields_to_update(self, repository):
        """Testa filtragem de campos para atualização"""
        update_data = {
            'videoId': {'S': 'video123'},
            'status': {'S': 'processing'},
            'retries': {'N': '1'}
        }
        result = repository._filter_fields_to_update(update_data)
        assert 'videoId' not in result
        assert 'status' in result
        assert 'retries' in result

    def test_filter_fields_to_update_empty(self, repository):
        """Testa filtragem quando não há campos para atualizar"""
        update_data = {'videoId': {'S': 'video123'}}
        with pytest.raises(ValueError, match="Nenhum campo para atualizar"):
            repository._filter_fields_to_update(update_data)

    def test_build_update_expression(self, repository):
        """Testa construção de expressão de atualização"""
        fields = {
            'status': {'S': 'processing'},
            'retries': {'N': '1'}
        }
        update_expr, expr_names, expr_values = repository._build_update_expression(fields)

        assert update_expr.startswith("SET")
        assert len(expr_names) == 2
        assert len(expr_values) == 2

    def test_execute_update_success(self, repository, mock_dynamodb_client):
        """Testa execução de update com sucesso"""
        mock_response = {
            'Attributes': {
                'videoId': {'S': 'video123'},
                'status': {'S': 'processing'}
            }
        }
        mock_dynamodb_client.update_item.return_value = mock_response

        result = repository._execute_update(
            'video123',
            'SET #field0 = :value0',
            {'#field0': 'status'},
            {':value0': {'S': 'processing'}}
        )

        assert result == mock_response['Attributes']
        mock_dynamodb_client.update_item.assert_called_once()

    def test_execute_update_not_found(self, repository, mock_dynamodb_client):
        """Testa execução de update quando item não é encontrado"""
        mock_dynamodb_client.update_item.return_value = {}

        with pytest.raises(ValueError, match="não encontrado"):
            repository._execute_update(
                'video999',
                'SET #field0 = :value0',
                {'#field0': 'status'},
                {':value0': {'S': 'processing'}}
            )

    def test_convert_to_dto(self, repository):
        """Testa conversão de item DynamoDB para DTO"""
        item = {
            'videoId': {'S': 'video456'},
            'fileName': {'S': 'convert_test.mp4'},
            'extensionFile': {'S': 'mp4'},
            'status': {'S': 'PROCESSING'},
            'created': {'S': '2026-01-27T12:00:00Z'},
            'userId': {'S': 'user456'},
            'totalTime': {'N': '7200'},
            'unitTime': {'S': 's'},
            'startTime': {'N': '0'},
            'endTime': {'N': '120'},
            'timeInterval': {'L': [{'S': '00:00:00'}, {'S': '00:02:00'}]},
            'maxRetry': {'N': '5'},
            'retries': {'N': '1'},
            'quality': {'S': 'ultra'},
            'logs': {'L': []}
        }

        result = repository._convert_to_dto(item)

        assert result.__class__.__name__ == 'VdscMetadataDTO'
        assert result.video_id == 'video456'
        assert result.file_name == 'convert_test.mp4'
        assert result.total_time == 7200

    def test_update_metadata_by_video_id_complete_flow(self, repository, mock_dynamodb_client):
        """Testa fluxo completo de atualização de metadados"""
        from core.dtos.vdsc_metadata_dto import LogEntryDTO

        dto = VdscMetadataDTO(
            video_id='video789',
            file_name='flow_test.mp4',
            extension_file='mp4',
            status='PROCESSING',
            created='2026-01-27T14:00:00Z',
            user_id='user789',
            total_time=1800,
            unit_time='s',
            start_time=0,
            end_time=30,
            time_interval=['00:00:00', '00:00:30'],
            max_retry=3,
            retries=1,
            quality='high',
            logs=[LogEntryDTO(timestamp='2026-01-27T14:00:00Z', info='Processing')]
        )

        mock_response = {
            'Attributes': {
                'videoId': {'S': 'video789'},
                'fileName': {'S': 'flow_test.mp4'},
                'extensionFile': {'S': 'mp4'},
                'status': {'S': 'PROCESSING'},
                'created': {'S': '2026-01-27T14:00:00Z'},
                'userId': {'S': 'user789'},
                'totalTime': {'N': '1800'},
                'unitTime': {'S': 's'},
                'startTime': {'N': '0'},
                'endTime': {'N': '30'},
                'timeInterval': {'L': [{'S': '00:00:00'}, {'S': '00:00:30'}]},
                'maxRetry': {'N': '3'},
                'retries': {'N': '1'},
                'quality': {'S': 'high'},
                'logs': {'L': [
                    {'M': {
                        'timestamp': {'S': '2026-01-27T14:00:00Z'},
                        'info': {'S': 'Processing'}
                    }}
                ]}
            }
        }
        mock_dynamodb_client.update_item.return_value = mock_response

        result = repository.update_metadata_by_video_id(dto)

        assert result.__class__.__name__ == 'VdscMetadataDTO'
        assert result.video_id == 'video789'
        assert result.status == 'PROCESSING'
        assert result.retries == 1
        mock_dynamodb_client.update_item.assert_called_once()

    def test_build_update_expression_multiple_fields(self, repository):
        """Testa construção de expressão com múltiplos campos"""
        fields = {
            'status': {'S': 'FINISHED'},
            'retries': {'N': '2'},
            'quality': {'S': 'ultra'},
            'logs': {'L': []}
        }

        update_expr, expr_names, expr_values = repository._build_update_expression(fields)

        assert 'SET' in update_expr
        assert len(expr_names) == 4
        assert len(expr_values) == 4
        assert all(f'#field{i}' in expr_names for i in range(4))
        assert all(f':value{i}' in expr_values for i in range(4))

    def test_update_metadata_with_exception_handling(self, repository, mock_dynamodb_client):
        """Testa tratamento de exceção durante atualização"""

        dto = VdscMetadataDTO(
            video_id='video_error',
            file_name='error_test.mp4',
            extension_file='mp4',
            status='FAILED',
            created='2026-01-27T15:00:00Z',
            user_id='user_error',
            total_time=600,
            unit_time='s',
            start_time=0,
            end_time=10,
            time_interval=['00:00:00'],
            max_retry=3,
            retries=3,
            quality='low',
            logs=[]
        )

        mock_dynamodb_client.update_item.side_effect = Exception("DynamoDB update error")

        with pytest.raises(Exception):
            repository.update_metadata_by_video_id(dto)

    def test_get_metadata_prints_log(self, repository, mock_dynamodb_client, capsys):
        """Testa se a função imprime log ao buscar metadados"""
        mock_response = {
            'Item': {
                'videoId': {'S': 'video_log'},
                'fileName': {'S': 'log_test.mp4'},
                'extensionFile': {'S': 'mp4'},
                'status': {'S': 'UPLOADED'},
                'created': {'S': '2026-01-27T16:00:00Z'},
                'userId': {'S': 'user_log'},
                'totalTime': {'N': '900'},
                'unitTime': {'S': 's'},
                'startTime': {'N': '0'},
                'endTime': {'N': '15'},
                'timeInterval': {'L': [{'S': '00:00:00'}]},
                'maxRetry': {'N': '3'},
                'retries': {'N': '0'},
                'quality': {'S': 'medium'},
                'logs': {'L': []}
            }
        }
        mock_dynamodb_client.get_item.return_value = mock_response

        repository.get_metadata_by_video_id('video_log')

        captured = capsys.readouterr()
        assert 'Buscando metadados para vídeo: video_log' in captured.out


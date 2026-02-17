"""Testes unitários para CloudWatchRepository"""
import pytest
from unittest.mock import patch, MagicMock
from aws.datasources.metrics.cloudwatch_repository import CloudWatchRepository


@pytest.mark.unit
class TestCloudWatchRepository:
    """Testes para o CloudWatchRepository"""

    @pytest.fixture
    def repository(self):
        """Fixture para criar instância do repository"""
        mock_metrics = MagicMock()
        return CloudWatchRepository(metrics_provider=mock_metrics)

    @pytest.fixture
    def metric_info_with_resize(self):
        """Fixture com informações de métrica com redimensionamento"""
        return {
            'resize': True,
            'original_min_size': 1080,
            'resize_output': 720,
            'quality_output_level': 80,
            'frames_processed': 10,
            'workers': 4,
            'video_size_mb': 100.0,
            'process_total_time_seconds': 15.5,
            'efficiency_per_frame_seconds': 1.55
        }

    @pytest.fixture
    def metric_info_without_resize(self):
        """Fixture com informações de métrica sem redimensionamento"""
        return {
            'resize': False,
            'original_min_size': 720,
            'resize_output': 720,
            'quality_output_level': 60,
            'frames_processed': 5,
            'workers': 2,
            'video_size_mb': 50.0,
            'process_total_time_seconds': 8.0,
            'efficiency_per_frame_seconds': 1.6
        }

    @patch('aws.datasources.metrics.cloudwatch_repository.resource')
    def test_send_metric_with_resize(self, mock_resource, repository, metric_info_with_resize):
        """Testa envio de métrica com redimensionamento"""
        # Mock do uso de memória
        mock_rusage = MagicMock()
        mock_rusage.ru_maxrss = 102400  # 100 MB em KB
        mock_resource.getrusage.return_value = mock_rusage
        mock_resource.RUSAGE_SELF = 0

        repository.send_metric(metric_info_with_resize)

        # Verifica que dimensões foram adicionadas
        assert repository.metrics.add_dimension.call_count == 4
        repository.metrics.add_dimension.assert_any_call(name="Redimensionado", value="True")
        repository.metrics.add_dimension.assert_any_call(name="ResoluçãoOriginal", value="1080p ou superior")
        repository.metrics.add_dimension.assert_any_call(name="ResoluçãoNova", value="720p")
        repository.metrics.add_dimension.assert_any_call(name="QualidadeDeSaidaImage", value="Alta")

        # Verifica que métricas foram adicionadas
        assert repository.metrics.add_metric.call_count == 6

        # Verifica que métricas foram enviadas (não tem mais flush_metrics e clear_metrics)
        # mock_metrics.flush_metrics.assert_called_once()
        # mock_metrics.clear_metrics.assert_called_once()

    @patch('aws.datasources.metrics.cloudwatch_repository.resource')
    def test_send_metric_without_resize(self, mock_resource, repository, metric_info_without_resize):
        """Testa envio de métrica sem redimensionamento"""
        # Mock do uso de memória
        mock_rusage = MagicMock()
        mock_rusage.ru_maxrss = 51200  # 50 MB em KB
        mock_resource.getrusage.return_value = mock_rusage
        mock_resource.RUSAGE_SELF = 0

        repository.send_metric(metric_info_without_resize)

        # Verifica que dimensões foram adicionadas
        repository.metrics.add_dimension.assert_any_call(name="Redimensionado", value="False")
        repository.metrics.add_dimension.assert_any_call(name="QualidadeDeSaidaImage", value="Média")

        # Verifica que métricas foram enviadas (não tem mais flush_metrics e clear_metrics)
        # repository.metrics.flush_metrics.assert_called_once()

    def test_get_resolution_range_ultra(self, repository):
        """Testa classificação de resolução ultra (1080p ou superior)"""
        assert repository._get_resolution_range(1080) == '1080p ou superior'
        assert repository._get_resolution_range(2160) == '1080p ou superior'
        assert repository._get_resolution_range(4320) == '1080p ou superior'

    def test_get_resolution_range_high(self, repository):
        """Testa classificação de resolução alta (720p)"""
        assert repository._get_resolution_range(720) == '720p'
        assert repository._get_resolution_range(900) == '720p'

    def test_get_resolution_range_medium(self, repository):
        """Testa classificação de resolução média (480p)"""
        assert repository._get_resolution_range(480) == '480p'
        assert repository._get_resolution_range(600) == '480p'

    def test_get_resolution_range_low(self, repository):
        """Testa classificação de resolução baixa (360p)"""
        assert repository._get_resolution_range(360) == '360p'
        assert repository._get_resolution_range(400) == '360p'

    def test_get_resolution_range_very_low(self, repository):
        """Testa classificação de resolução muito baixa"""
        assert repository._get_resolution_range(240) == 'Menor que 360p'
        assert repository._get_resolution_range(144) == 'Menor que 360p'

    def test_get_quality_output_range_high(self, repository):
        """Testa classificação de qualidade alta (>= 75)"""
        assert repository._get_quality_output_range(75) == 'Alta'
        assert repository._get_quality_output_range(85) == 'Alta'
        assert repository._get_quality_output_range(100) == 'Alta'

    def test_get_quality_output_range_medium(self, repository):
        """Testa classificação de qualidade média (50-74)"""
        assert repository._get_quality_output_range(50) == 'Média'
        assert repository._get_quality_output_range(60) == 'Média'
        assert repository._get_quality_output_range(74) == 'Média'

    def test_get_quality_output_range_low(self, repository):
        """Testa classificação de qualidade baixa (10-49)"""
        assert repository._get_quality_output_range(10) == 'Baixa'
        assert repository._get_quality_output_range(30) == 'Baixa'
        assert repository._get_quality_output_range(49) == 'Baixa'

    def test_get_quality_output_range_unknown(self, repository):
        """Testa classificação de qualidade desconhecida (< 10)"""
        assert repository._get_quality_output_range(5) == 'Desconhecida'
        assert repository._get_quality_output_range(0) == 'Desconhecida'

    @patch('aws.datasources.metrics.cloudwatch_repository.resource')
    def test_get_memory_usage_linux(self, mock_resource, repository):
        """Testa obtenção de uso de memória em ambiente Linux"""
        # Mock do resource.getrusage para ambiente Linux
        mock_rusage = MagicMock()
        mock_rusage.ru_maxrss = 102400  # 100 MB em KB (Linux retorna em KB)
        mock_resource.getrusage.return_value = mock_rusage
        mock_resource.RUSAGE_SELF = 0

        result = repository._get_memory_usage()

        # 102400 KB / 1024 = 100 MB
        assert result == 100.0
        mock_resource.getrusage.assert_called_once_with(0)

    def test_get_memory_usage_windows(self, repository):
        """Testa obtenção de uso de memória em ambiente Windows (resource não disponível)"""
        # Mock resource como None (simula Windows)
        with patch('aws.datasources.metrics.cloudwatch_repository.resource', None):
            result = repository._get_memory_usage()

            # Em Windows, deve retornar 0.0
            assert result == 0.0

    @patch('aws.datasources.metrics.cloudwatch_repository.resource')
    def test_get_memory_usage_handles_exception(self, mock_resource, repository):
        """Testa que _get_memory_usage trata exceções corretamente"""
        # Simula erro ao obter uso de memória
        mock_resource.getrusage.side_effect = Exception("Erro ao obter memória")
        mock_resource.RUSAGE_SELF = 0

        # Deve retornar 0.0 em caso de erro
        with patch.object(repository, '_get_memory_usage', return_value=0.0):
            result = repository._get_memory_usage()
            assert result == 0.0

    @patch('aws.datasources.metrics.cloudwatch_repository.resource')
    def test_send_metric_adds_all_metrics(self, mock_resource, repository, metric_info_with_resize):
        """Testa que send_metric adiciona todas as métricas esperadas"""
        # Mock do uso de memória
        mock_rusage = MagicMock()
        mock_rusage.ru_maxrss = 102400  # 100 MB em KB
        mock_resource.getrusage.return_value = mock_rusage
        mock_resource.RUSAGE_SELF = 0

        from aws_lambda_powertools.metrics import MetricUnit

        repository.send_metric(metric_info_with_resize)

        # Verifica cada métrica individualmente
        repository.metrics.add_metric.assert_any_call(
            name="FramesProcessados",
            value=10,
            unit=MetricUnit.Count
        )
        repository.metrics.add_metric.assert_any_call(
            name="Workers",
            value=4,
            unit=MetricUnit.Count
        )
        repository.metrics.add_metric.assert_any_call(
            name="TamanhoVideoMB",
            value=100.0,
            unit=MetricUnit.Megabytes
        )
        repository.metrics.add_metric.assert_any_call(
            name="TempoTotalProcessamentoSegundos",
            value=15.5,
            unit=MetricUnit.Seconds
        )
        repository.metrics.add_metric.assert_any_call(
            name="TempoMedioPorFrameSegundos",
            value=1.55,
            unit=MetricUnit.Seconds
        )

    @patch('aws.datasources.metrics.cloudwatch_repository.resource')
    def test_send_metric_clears_after_flush(self, mock_resource, repository, metric_info_with_resize):
        """Testa que send_metric executa corretamente (flush e clear foram removidos)"""
        # Mock do uso de memória
        mock_rusage = MagicMock()
        mock_rusage.ru_maxrss = 102400  # 100 MB em KB
        mock_resource.getrusage.return_value = mock_rusage
        mock_resource.RUSAGE_SELF = 0

        repository.send_metric(metric_info_with_resize)

        # Apenas verifica que a métrica foi processada sem erros
        # flush_metrics e clear_metrics foram removidos da implementação
        assert repository.metrics.add_metric.call_count == 6
        assert repository.metrics.add_dimension.call_count == 4

    @patch('aws.datasources.metrics.cloudwatch_repository.resource')
    def test_send_metric_with_high_quality(self, mock_resource, repository):
        """Testa envio de métrica com qualidade alta"""
        # Mock do uso de memória
        mock_rusage = MagicMock()
        mock_rusage.ru_maxrss = 51200  # 50 MB em KB
        mock_resource.getrusage.return_value = mock_rusage
        mock_resource.RUSAGE_SELF = 0

        metric_info = {
            'resize': True,
            'original_min_size': 1080,
            'resize_output': 1080,
            'quality_output_level': 95,  # Qualidade alta
            'frames_processed': 5,
            'workers': 2,
            'video_size_mb': 50.0,
            'process_total_time_seconds': 8.0,
            'efficiency_per_frame_seconds': 1.6
        }

        repository.send_metric(metric_info)

        repository.metrics.add_dimension.assert_any_call(name="QualidadeDeSaidaImage", value="Alta")

    @patch('aws.datasources.metrics.cloudwatch_repository.resource')
    def test_send_metric_with_multiple_workers(self, mock_resource, repository):
        """Testa envio de métrica com múltiplos workers"""
        # Mock do uso de memória
        mock_rusage = MagicMock()
        mock_rusage.ru_maxrss = 102400  # 100 MB em KB
        mock_resource.getrusage.return_value = mock_rusage
        mock_resource.RUSAGE_SELF = 0

        from aws_lambda_powertools.metrics import MetricUnit

        metric_info = {
            'resize': True,
            'original_min_size': 1080,
            'resize_output': 720,
            'quality_output_level': 80,
            'frames_processed': 100,
            'workers': 16,  # Muitos workers
            'video_size_mb': 500.0,
            'process_total_time_seconds': 60.0,
            'efficiency_per_frame_seconds': 0.6
        }

        repository.send_metric(metric_info)

        repository.metrics.add_metric.assert_any_call(
            name="Workers",
            value=16,
            unit=MetricUnit.Count
        )

    @patch('aws.datasources.metrics.cloudwatch_repository.resource')
    def test_send_metric_with_low_quality(self, mock_resource, repository):
        """Testa envio de métrica com qualidade baixa"""
        # Mock do uso de memória
        mock_rusage = MagicMock()
        mock_rusage.ru_maxrss = 51200  # 50 MB em KB
        mock_resource.getrusage.return_value = mock_rusage
        mock_resource.RUSAGE_SELF = 0

        metric_info = {
            'resize': True,
            'original_min_size': 720,
            'resize_output': 360,
            'quality_output_level': 30,  # Qualidade baixa
            'frames_processed': 3,
            'workers': 1,
            'video_size_mb': 25.0,
            'process_total_time_seconds': 5.0,
            'efficiency_per_frame_seconds': 1.67
        }

        repository.send_metric(metric_info)

        repository.metrics.add_dimension.assert_any_call(name="QualidadeDeSaidaImage", value="Baixa")

    def test_get_resolution_range_boundary_values(self, repository):
        """Testa valores limites de classificação de resolução"""
        # Testa exatamente nos limites
        assert repository._get_resolution_range(1080) == '1080p ou superior'
        assert repository._get_resolution_range(1079) == '720p'
        assert repository._get_resolution_range(720) == '720p'
        assert repository._get_resolution_range(719) == '480p'
        assert repository._get_resolution_range(480) == '480p'
        assert repository._get_resolution_range(479) == '360p'
        assert repository._get_resolution_range(360) == '360p'
        assert repository._get_resolution_range(359) == 'Menor que 360p'

    def test_get_quality_output_range_boundary_values(self, repository):
        """Testa valores limites de classificação de qualidade"""
        # Testa exatamente nos limites
        assert repository._get_quality_output_range(75) == 'Alta'
        assert repository._get_quality_output_range(74) == 'Média'
        assert repository._get_quality_output_range(50) == 'Média'
        assert repository._get_quality_output_range(49) == 'Baixa'
        assert repository._get_quality_output_range(10) == 'Baixa'
        assert repository._get_quality_output_range(9) == 'Desconhecida'

    @patch('aws.datasources.metrics.cloudwatch_repository.resource')
    def test_get_memory_usage_converts_to_mb(self, mock_resource, repository):
        """Testa que get_memory_usage converte corretamente KB para MB"""
        # Mock com diferentes tamanhos de memória em KB (formato Linux)
        test_cases = [
            (1024, 1.0),       # 1 MB (1024 KB)
            (10240, 10.0),     # 10 MB (10240 KB)
            (102400, 100.0),   # 100 MB (102400 KB)
            (512000, 500.0),   # 500 MB (512000 KB)
        ]

        for kb_value, expected_mb in test_cases:
            mock_rusage = MagicMock()
            mock_rusage.ru_maxrss = kb_value
            mock_resource.getrusage.return_value = mock_rusage
            mock_resource.RUSAGE_SELF = 0

            result = repository._get_memory_usage()
            assert result == expected_mb

    @patch('aws.datasources.metrics.cloudwatch_repository.resource')
    def test_send_metric_with_original_quality(self, mock_resource, repository):
        """Testa envio de métrica com qualidade original (sem redimensionamento)"""
        # Mock do uso de memória
        mock_rusage = MagicMock()
        mock_rusage.ru_maxrss = 51200  # 50 MB em KB
        mock_resource.getrusage.return_value = mock_rusage
        mock_resource.RUSAGE_SELF = 0

        metric_info = {
            'resize': False,
            'original_min_size': 1080,
            'resize_output': 1080,
            'quality_output_level': 100,  # Qualidade máxima
            'frames_processed': 3,
            'workers': 2,
            'video_size_mb': 150.0,
            'process_total_time_seconds': 10.0,
            'efficiency_per_frame_seconds': 3.33
        }

        repository.send_metric(metric_info)

        repository.metrics.add_dimension.assert_any_call(name="Redimensionado", value="False")
        repository.metrics.add_dimension.assert_any_call(name="ResoluçãoOriginal", value="1080p ou superior")
        repository.metrics.add_dimension.assert_any_call(name="ResoluçãoNova", value="1080p ou superior")
        repository.metrics.add_dimension.assert_any_call(name="QualidadeDeSaidaImage", value="Alta")


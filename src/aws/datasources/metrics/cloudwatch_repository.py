import logging
try:
    import resource
except ImportError:
    resource = None #Cenário de testes locais

from aws.datasources.metrics.cloudwatch_interface import CloudWatchInterface
from aws_lambda_powertools import Metrics
from aws_lambda_powertools.metrics import MetricUnit

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CloudWatchRepository(CloudWatchInterface):

    def __init__(self, metrics_provider: Metrics):
        self.metrics = metrics_provider

    def send_metric(self, metric_info: str):

        logger.debug(f"Enviando métricas para CloudWatch: {metric_info}")

        try:
            # Converte todos os valores para tipos Python nativos
            resize = bool(metric_info['resize'])
            original_min_size = int(metric_info['original_min_size'])
            resize_output = int(metric_info['resize_output'])
            quality_output_level = int(metric_info['quality_output_level'])
            frames_processed = int(metric_info['frames_processed'])
            workers = int(metric_info['workers'])
            video_size_mb = float(metric_info['video_size_mb'])
            process_total_time = float(metric_info['process_total_time_seconds'])
            efficiency_per_frame = float(metric_info['efficiency_per_frame_seconds'])
        except (TypeError, ValueError, KeyError) as e:
            logger.error(f"Erro ao converter valores de metric_info: {e}. metric_info={metric_info}", exc_info=True)
            raise

        # Adiciona dimensões
        self.metrics.add_dimension(name="Redimensionado", value=str(resize))
        self.metrics.add_dimension(name="ResoluçãoOriginal", value=self._get_resolution_range(original_min_size))
        self.metrics.add_dimension(name="QualidadeDeSaidaImage", value=self._get_quality_output_range(quality_output_level))
        self.metrics.add_dimension(name="ResoluçãoNova", value=self._get_resolution_range(resize_output))
        logger.debug("Dimensões adicionadas com sucesso")


        # Adiciona métricas
        self.metrics.add_metric(name="FramesProcessados", value=frames_processed, unit=MetricUnit.Count)
        self.metrics.add_metric(name="Workers", value=workers, unit=MetricUnit.Count)
        self.metrics.add_metric(name="TamanhoVideoMB", value=video_size_mb, unit=MetricUnit.Megabytes)
        self.metrics.add_metric(name="TempoTotalProcessamentoSegundos", value=process_total_time, unit=MetricUnit.Seconds)
        self.metrics.add_metric(name="TempoMedioPorFrameSegundos", value=efficiency_per_frame, unit=MetricUnit.Seconds)
        self.metrics.add_metric(name="UsoMemoriaMB", value=float(self._get_memory_usage()), unit=MetricUnit.Megabytes)
        logger.debug("Métricas adicionadas com sucesso")

        logger.debug("Métricas processadas com sucesso")

    def _get_resolution_range(self, resolution) -> str:
        """Converte resolução para categoria de qualidade"""
        try:
            resolution = int(resolution)
        except (TypeError, ValueError) as e:
            logger.warning(f"Erro ao converter resolução '{resolution}' para int: {e}. Usano valor padrão 0.")
            resolution = 0

        if resolution >= 1080:
            return '1080p ou superior'
        if resolution >= 720:
            return '720p'
        if resolution >= 480:
            return '480p'
        if resolution >= 360:
            return '360p'
        if resolution == 0:
            return 'Sem Redimensionamento'
        return 'Menor que 360p'

    def _get_quality_output_range(self, quality_output_level) -> str:
        """Converte nível de qualidade (inteiro de 10 a 100) para categoria"""
        try:
            quality_output_level = int(quality_output_level)
        except (TypeError, ValueError) as e:
            logger.warning(f"Erro ao converter quality_output_level '{quality_output_level}' para int: {e}. Usando valor padrão 75.")
            quality_output_level = 75

        if quality_output_level >= 75:
            return 'Alta'
        if quality_output_level >= 50:
            return 'Média'
        if quality_output_level >= 10:
            return 'Baixa'
        return 'Desconhecida'

    def _get_memory_usage(self):
        if resource is None:
            return 0.0
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024




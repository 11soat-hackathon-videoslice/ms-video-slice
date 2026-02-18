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

    def send_metric(self, metric_info: dict):
        logger.debug(f"Enviando métricas para CloudWatch: {metric_info}")

        try:
            # Conversões seguras
            resize = "Sim" if bool(metric_info.get('resize')) else "Nao"
            original_min_size = int(metric_info.get('original_min_size', 0))
            resize_output = int(metric_info.get('resize_output', 0))
            quality_output_level = int(metric_info.get('quality_output_level', 75))

            frames_processed = int(metric_info.get('frames_processed', 0))
            workers = int(metric_info.get('workers', 0))
            video_size_mb = float(metric_info.get('video_size_mb', 0.0))
            process_total_time = float(metric_info.get('process_total_time_seconds', 0.0))
            efficiency_per_frame = float(metric_info.get('efficiency_per_frame_seconds', 0.0))
            memory_usage = float(self._get_memory_usage())

            self.metrics.set_dimensions({
                "Redimensionado": resize,
                "ResolucaoOriginal": self._get_resolution_range(original_min_size),
                "QualidadeSaida": self._get_quality_output_range(quality_output_level),
                "ResolucaoNova": self._get_resolution_range(resize_output),
                "Service": "VideoSlice"
            })

            # 2. Adicionar métricas
            self.metrics.add_metric(name="FramesProcessados", value=frames_processed, unit=MetricUnit.Count)
            self.metrics.add_metric(name="WorkersCount", value=workers, unit=MetricUnit.Count)
            self.metrics.add_metric(name="TamanhoVideoMB", value=video_size_mb, unit=MetricUnit.Megabytes)
            self.metrics.add_metric(name="TempoTotalProcessamento", value=process_total_time, unit=MetricUnit.Seconds)
            self.metrics.add_metric(name="TempoMedioPorFrame", value=efficiency_per_frame, unit=MetricUnit.Seconds)
            self.metrics.add_metric(name="UsoMemoriaMB", value=memory_usage, unit=MetricUnit.Megabytes)

            logger.debug("Métricas e Dimensões preparadas para o flush do Powertools")

        except Exception as e:
            logger.error(f"Erro ao processar métricas: {e}", exc_info=True)


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




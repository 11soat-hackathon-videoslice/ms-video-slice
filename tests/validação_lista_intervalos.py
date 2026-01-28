import logging

from aws.datasources.database.dynamodb_repository import DynamoDBRepository
from aws.datasources.storage.s3_repository import S3StorageRepository
from aws.datasources.producer.event_producer import EventProducer
from aws.dataproxy.vdsc_dataproxy import VdscDataProxy
from aws.config.vdsc_config import VdscConfig
from core.adapters.vdsc_gateway import VdscGateway

from core.dtos import VdscMetadataDTO
from core.adapters.vdsc_controller import VdscController
from aws.handler.vdsc_exception_handler import VdscExceptionHandler


from aws.handler.vdsc_exception_handler import VdscExceptionHandler
from src import VdscProcessUseCase, VdscMetadata

### Injeção de dependências ####
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config = VdscConfig()
dynamodb_repository = DynamoDBRepository(config.dynamodb['table_name'], config.aws['region'])
s3_repository = S3StorageRepository(config.s3_bucket['name'], config.aws['region'])
event_producer = EventProducer()
vdsc_handler= VdscExceptionHandler()

def validar_lista_intervalos():
    dto = VdscMetadataDTO(
        video_id="video123",
        file_name="test_video.mp4",
        extension_file="mp4",
        status="UPLOADED",
        created="2026-01-13T00:00:00Z",
        user_id="user123",
        total_time=3600,
        unit_time="ms",
        start_time=500,
        end_time=10000,
        time_interval=[500,1000,1500,2000,2500,3000,3500,4000,4500,5000,5500,6000,6500,7000,7500,8000,8500,9000,9500,10000],
        max_retry=3,
        retries=0,
        quality="high",
        logs=[]
    )


    dataproxy = VdscDataProxy(dynamodb_repository, s3_repository, event_producer)
    gateway = VdscGateway(dataproxy)
    metadata = VdscMetadata(dto=dto)
    use_case = VdscProcessUseCase()

     # Obtém o multiplicador de unidade de tempo
    time_unit_multiplier = use_case._get_multiplier_time_unit(metadata.unit_time)
    list = use_case._create_interval_list(vdsc_metadata=metadata,time_unit_multiplier=time_unit_multiplier)
    print(list)

def test_validar_lista_intervalos():
    """Testa a validação de uma lista de intervalos de tempo."""
    try:
        validar_lista_intervalos()
        print("Validação bem-sucedida.")
    except ValueError as e:
        print(f"Erro de validação: {e}")

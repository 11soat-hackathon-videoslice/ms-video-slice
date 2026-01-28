import json
import logging
from typing import Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor


# Imports absolutos (funcionam tanto localmente quanto na Lambda)
from aws.datasources.database.dynamodb_repository import DynamoDBRepository
from aws.datasources.storage.s3_repository import S3StorageRepository
from aws.datasources.producer.event_producer import EventProducer
from aws.dataproxy.vdsc_dataproxy import VdscDataProxy
from aws.config.vdsc_config import VdscConfig

from core.dtos import VdscMetadataDTO
from core.adapters.vdsc_controller import VdscController
from aws.handler.vdsc_exception_handler import VdscExceptionHandler

### Injeção de dependências ####
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
config = VdscConfig()
dynamodb_repository = DynamoDBRepository(config.dynamodb['table_name'], config.aws['region'])
s3_repository = S3StorageRepository(config.s3_bucket['name'], config.aws['region'])
event_producer = EventProducer()
vdsc_handler= VdscExceptionHandler()
executor = ThreadPoolExecutor(max_workers=config.vdsc['max_workers'])
max_timeout = config.vdsc['max_timeout']


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    logger.info(f"Recebido evento do DynamoDB: {json.dumps(event)}")

    try:
        records = event['Records']
        if not records:
            logger.warning("Registro vazio encontrado no evento. Pulando processamento deste registro.")
            return {'statusCode': 200, 'body': json.dumps({'error': 'Registro vazio no evento'})}

        asyncio.run(process_record_aync(records))

        return {'statusCode': 200, 'body': json.dumps({'message': 'Iniciado processamento assíncrono de de eventos'})}

    except asyncio.TimeoutError:
        logger.error("Timeout ao processar eventos - tempo limite de 5 minutos excedido")
        return {
            'statusCode': 408,
            'body': json.dumps({'error': 'Timeout ao processar eventos'})
        }
    except Exception as ex:
        logger.error(f"Erro inesperado ao processar evento: {str(ex)}", exc_info=ex)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(ex)})
        }

def process_video_async(event_dto: VdscMetadataDTO) -> None:
    """Processa o vídeo de forma síncrona (será executado em thread separada)"""
    try:

        dataproxy = VdscDataProxy(dynamodb=dynamodb_repository, s3=s3_repository, event_producer=event_producer)
        vdsc_controller = VdscController(dataproxy=dataproxy, handler=vdsc_handler)
        vdsc_controller.video_slice_processing(event_dto, config)
        logger.info(f"Processamento concluído para vídeo ID: {event_dto.video_id}")

    except Exception as ex:
        logger.error(f"Erro ao processar vídeo {event_dto.video_id}: {str(ex)}", exc_info=ex)

async def process_record_aync(records:list) -> None:
    async_loop = asyncio.get_event_loop()
    tasks = []

    for record in records:
        event_dto = VdscMetadataDTO.from_dynamodb_item(record['dynamodb']['NewImage'])
        event_dto.validate()
        logger.info(f"Metadados válidos para vídeo ID: {event_dto.video_id}")

        # Executar processamento em thread separada
        task = async_loop.run_in_executor(executor, process_video_async, event_dto)
        tasks.append(task)

    if tasks:
        await asyncio.wait(asyncio.gather(*tasks,return_exceptions=True),timeout=max_timeout)


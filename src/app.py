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
    """Handler principal da Lambda para processamento de eventos do DynamoDB"""
    logger.info(f"Recebido evento do DynamoDB: {json.dumps(event)}")

    try:
        records = event['Records']
        if not records:
            logger.warning("Registro vazio encontrado no evento. Pulando processamento deste registro.")
            return {'statusCode': 200, 'body': json.dumps({'error': 'Registro vazio no evento'})}

        # Executar processamento assíncrono e aguardar resultados
        results = asyncio.run(process_record_aync(records))

        # Verificar se houve erros durante o processamento
        errors = [r for r in results if isinstance(r, Exception)]
        if errors:
            logger.error(f"Erros encontrados durante processamento: {len(errors)} de {len(results)} falharam")
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': f'{len(errors)} vídeo(s) falharam no processamento',
                    'details': [str(e) for e in errors]
                })
            }

        return {'statusCode': 200, 'body': json.dumps({'message': f'Processamento concluído com sucesso para {len(results)} vídeo(s)'})}

    except asyncio.TimeoutError:
        logger.error(f"Timeout ao processar eventos - tempo limite de {max_timeout} segundos excedido")
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
        # Re-lançar exceção para que seja capturada pelo gather com return_exceptions=True
        raise

async def process_record_aync(records: list) -> list:
    """Processa registros do DynamoDB de forma assíncrona e retorna lista de resultados"""
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
        # Usar wait_for com gather para aplicar timeout e coletar resultados
        try:
            results = await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=max_timeout)
            return results
        except asyncio.TimeoutError:
            logger.error(f"Timeout ao processar {len(tasks)} vídeos após {max_timeout} segundos")
            raise

    return []

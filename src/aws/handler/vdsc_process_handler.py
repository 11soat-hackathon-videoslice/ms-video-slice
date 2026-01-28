import json
import logging
from typing import Dict, Any

from ..datasources.database.dynamodb_repository import DynamoDBRepository
from ..datasources.storage.s3_repository import S3StorageRepository
from ..datasources.producer.event_producer import EventProducer
from ..dataproxy.vdsc_dataproxy import VdscDataProxy
from ..config.vdsc_config import VdscConfig

from ...core.dtos import VdscMetadataDTO
from ...core.adapters.vdsc_controller import VdscController
from .vdsc_exception_handler import VdscExceptionHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
config = VdscConfig()
dynamodb_repository = DynamoDBRepository(config.dynamodb['table_name'], config.aws['region'])
s3_repository = S3StorageRepository(config.s3_bucket['name'], config.aws['region'])
event_producer = EventProducer()
vdsc_handler= VdscExceptionHandler()


def vdsc_process_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:

    logger.info(f"Recebido evento do DynamoDB: {json.dumps(event)}")

    try:
        for record in event['Records']:
            event_dto = VdscMetadataDTO.from_dynamodb_item(record['dynamodb']['NewImage'])

            event_dto.validate()
            logger.info(f"Metadados válidos para vídeo ID: {event_dto.video_id}")


            dataproxy = VdscDataProxy(dynamodb=dynamodb_repository, s3=s3_repository, event_producer=event_producer)
            vdsc_controller = VdscController(dataproxy=dataproxy, handler=vdsc_handler)
            vdsc_controller.video_slice_processing(event_dto, config)

    except Exception as ex:
        logger.error(f"Erro inesperado ao processar evento: {str(ex)}", exc_info=ex)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(ex)
            })
        }

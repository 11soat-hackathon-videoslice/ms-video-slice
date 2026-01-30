import json
import logging
from typing import Dict, Any
from aws_lambda_powertools.utilities.data_classes import DynamoDBStreamEvent
from aws_lambda_powertools.utilities.idempotency import (IdempotencyConfig, DynamoDBPersistenceLayer, idempotent_function)

# Importação de dependências via módulo vdsc_config
from aws.config.vdsc_config import controller, config, async_events_queue
from core.dtos import VdscMetadataDTO

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#Configuração da camada de persistência para idempotência
persistence_layer  = DynamoDBPersistenceLayer(table_name="VideoSliceIdempotencyTable")
idempotent_config = IdempotencyConfig(event_key_jmespath="eventID", use_local_cache=True, local_cache_max_items=100)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handler principal da Lambda para processamento de eventos do DynamoDB"""
    logger.info(f"Recebido evento do DynamoDB: {json.dumps(event)}")
    idempotent_config.register_lambda_context(context)

    records = list(DynamoDBStreamEvent(event).records)
    for record in records:
        process_new_event(record=record)

    return {'statusCode': 202, 'body': json.dumps({"status": f"Recebido {len(records)} evento(s) para processamento."})}

@idempotent_function(persistence_store=persistence_layer,config=idempotent_config,data_keyword_argument="record")
def process_new_event(record):
    logger.info(f"Enfileirando evento {record.event_id} do video {record.dynamodb.new_image.get('videoId')}")
    async_events_queue.put((_process_video_event, record))

def _process_video_event(record):
    vdsc_metadata = None

    try:
        new_image = record.dynamodb.new_image
        vdsc_metadata = VdscMetadataDTO.from_dynamodb_item(new_image)
        logger.info(f"Processando vídeo ID: {vdsc_metadata.video_id}")
        controller.video_slice_processing(vdsc_metadata, config.vdsc)
        logger.info(f"Processamento concluído para vídeo ID: {vdsc_metadata.video_id}")

    except Exception as e:
        video_id = vdsc_metadata.video_id if vdsc_metadata else 'desconhecido'
        logger.error(f"Erro ao processar vídeo ID: {video_id} - {str(e)}")
        controller.handler.handle_exception(e, vdsc_metadata)

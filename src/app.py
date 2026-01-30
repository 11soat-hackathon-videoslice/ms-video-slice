import json, logging, threading, os
from typing import Dict, Any

import requests
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

def process_async_loop(ext_id):
    """Loop da extensão que mantém a Lambda viva até processar a fila"""
    while True:
        # Avisa a AWS: 'Pode mandar o próximo evento ou me congelar'
        # Mas a extensão só faz isso quando a fila interna esvaziar
        requests.get(
            f"http://{os.environ['AWS_LAMBDA_RUNTIME_API']}/2020-01-01/extension/event/next",
            headers={'Lambda-Extension-Identifier': ext_id},
            timeout=None
        )

        try:
            # Processa o que está na fila antes de liberar o congelamento
            while not async_events_queue.empty():
                task_func, data = async_events_queue.get_nowait()
                try:
                    task_func(data)
                except Exception as e:
                    logger.error(f"Erro ao processar tarefa assíncrona {e}")
                finally:
                    async_events_queue.task_done()
            requests.get(f"http://{os.environ['AWS_LAMBDA_RUNTIME_API']}/2020-01-01/extension/event/next",
                        headers={'Lambda-Extension-Identifier': ext_id},
                        timeout=None
                         )
        except Exception as e:
            logger.error(f"Erro no loop da extensão: {e}")


# Registro da Extensão no Warm Start
def init_extension():

    if os.environ.get('AWS_LAMBDA_RUNTIME_API') is None:
        logger.info("AWS_LAMBDA_RUNTIME_API não está definido. A extensão não será iniciada.")
        return
    try:
        res = requests.post(
            f"http://{os.environ['AWS_LAMBDA_RUNTIME_API']}/2020-01-01/extension/register",
            json={'events': ['INVOKE']},
            headers={'Lambda-Extension-Name': 'InternalAsyncExt'}
        )
        ext_id = res.headers['Lambda-Extension-Identifier']
        threading.Thread(target=process_async_loop, args=(ext_id,), daemon=True).start()
    except Exception as e:
        logger.error(f"Falha ao iniciar extensão: {e}")

init_extension()

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

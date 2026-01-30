import json, logging, threading, os, shutil, queue
from typing import Dict, Any

import requests
from aws_lambda_powertools.utilities.data_classes import DynamoDBStreamEvent
from aws_lambda_powertools.utilities.data_classes.dynamo_db_stream_event import DynamoDBRecord
from aws_lambda_powertools.utilities.idempotency import (IdempotencyConfig, DynamoDBPersistenceLayer, idempotent_function)

# Importação de dependências via módulo vdsc_config
from aws.config.vdsc_config import controller, config
from core.dtos import VdscMetadataDTO

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async_events_queue = queue.Queue()

#Configuração da camada de persistência para idempotência
persistence_layer  = DynamoDBPersistenceLayer(table_name="VideoSliceIdempotencyTable")
idempotent_config = IdempotencyConfig(event_key_jmespath="eventID", use_local_cache=True, local_cache_max_items=100)

def process_async_loop(ext_id):
    """Loop da extensão que mantém a Lambda viva até processar a fila"""

    logger.info("Iniciando loop da extensão...")
    try:
        requests.get(
            f"http://{os.environ['AWS_LAMBDA_RUNTIME_API']}/2020-01-01/extension/event/next",
            headers={'Lambda-Extension-Identifier': ext_id},
            timeout=None
        )
        logger.info("Extensão iniciada e aguardando eventos...")
    except Exception as e:
        logger.error(f"Erro ao conectar com Lambda Runtime API no init: {e}")
        return

    while True:
        try:
            logger.info("Aguardando eventos assíncronos na fila...")
            while not async_events_queue.empty():
                logger.info("Processando evento assíncrono da fila...")
                task_func, data = async_events_queue.get_nowait()
                try:
                    logger.info("Executando tarefa assíncrona...")
                    task_func(data)
                except Exception as e:
                    logger.error(f"Erro ao processar tarefa assíncrona: {e}", exc_info=True)
                finally:
                    logger.info("Finalizando fila de tarefas assíncrona...")
                    async_events_queue.task_done()
                    logger.info("Fila de tarefas finalizada.")

            logger.info("Antes de aguardar próximo evento...")

            response = requests.get(
                f"http://{os.environ['AWS_LAMBDA_RUNTIME_API']}/2020-01-01/extension/event/next",
                headers={'Lambda-Extension-Identifier': ext_id},
                timeout=None
            )
            logger.info(f"Próximo evento recebido. Status: {response.status_code}")

        except Exception as e:
            logger.error(f"Erro no loop da extensão: {e}", exc_info=True)
            # Aguarda um pouco antes de tentar novamente
            import time
            time.sleep(1)


# Registro da Extensão no Warm Start
def init_extension():
    logger.info("Iniciando registro da extensão...")

    if os.environ.get('AWS_LAMBDA_RUNTIME_API') is None:
        logger.info("AWS_LAMBDA_RUNTIME_API não está definido. A extensão não será iniciada.")
        return
    try:
        logger.info("Registrando extensão na AWS Lambda...")
        res = requests.post(
            f"http://{os.environ['AWS_LAMBDA_RUNTIME_API']}/2020-01-01/extension/register",
            json={'events': ['INVOKE']},
            headers={'Lambda-Extension-Name': 'InternalAsyncExt'},
            timeout=5
        )

        logger.info(f"Resposta do registro: Status Code={res.status_code}, Headers={res.headers}")

        # Verificar a chave correta do header
        if 'Lambda-Extension-Identifier' not in res.headers:
            logger.error(f"Header 'Lambda-Extension-Identifier' não encontrado. Headers disponíveis: {list(res.headers.keys())}")
            return

        ext_id = res.headers['Lambda-Extension-Identifier']
        logger.info(f"Extensão registrada com sucesso. ID: {ext_id}")
        threading.Thread(target=process_async_loop, args=(ext_id,), daemon=True).start()
    except requests.exceptions.Timeout:
        logger.error("Timeout ao registrar extensão na AWS Lambda")
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro de requisição ao iniciar extensão: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Falha ao iniciar extensão: {e}", exc_info=True)



def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handler principal da Lambda para processamento de eventos do DynamoDB"""
    logger.info("=== Iniciando Lambda Handler ===")
    init_extension()
    logger.info(f"Recebido evento do DynamoDB: {json.dumps(event)}")
    idempotent_config.register_lambda_context(context)

    try:
        records = list(DynamoDBStreamEvent(event).records)
        logger.info(f"Total de registros a processar: {len(records)}")

        for idx, record in enumerate(records):
            logger.info(f"Processando registro {idx + 1}/{len(records)}")
            process_new_event(record_raw=record.raw_event)

        return {'statusCode': 202, 'body': json.dumps({"status": f"Recebido {len(records)} evento(s) para processamento."})}
    except Exception as e:
        logger.error(f"Erro ao processar eventos do DynamoDB: {e}", exc_info=True)
        return {'statusCode': 500, 'body': json.dumps({"error": str(e)})}

@idempotent_function(persistence_store=persistence_layer,config=idempotent_config,data_keyword_argument="record_raw")
def process_new_event(record_raw):
    record = DynamoDBRecord(record_raw)
    video_id = record.dynamodb.new_image.get('videoId', 'desconhecido')
    logger.info(f"Enfileirando evento {record.event_id} do video {video_id}")
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
        logger.error(f"Erro ao processar vídeo ID: {video_id} - {str(e)}", exc_info=True)
        try:
            controller.handler.handle_exception(e, vdsc_metadata)
        except Exception as handler_error:
            logger.error(f"Erro ao processar exception handler: {handler_error}", exc_info=True)
    finally:
        _clean_file_system()

def _clean_file_system():
    for filename in os.listdir('/tmp'):
        file_path = os.path.join('/tmp', filename)
        try:
            logger.info(f"Removendo {file_path}")
            if os.path.isfile(file_path): os.unlink(file_path)
            elif os.path.isdir(file_path): shutil.rmtree(file_path)
        except Exception as e:
            logger.warning(f"Não foi possível remover {file_path}: {e}")
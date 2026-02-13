import json, logging, os, shutil
from typing import Dict, Any

# Importação de dependências via módulo vdsc_config
from aws.config.slice_config import controller, config
from core.dtos import VdscMetadataDTO

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handler principal da Lambda para processamento de eventos do DynamoDB"""

    logger.info("=== Iniciando Lambda Handler ===")
    logger.info(f"Recebido novo evento: {json.dumps(event)}")

    records = list(event.get('Records', []))
    logger.info(f"Total de registros a processar: {len(records)}")

    for record in records:
        try:
            body_raw = record.get('body', '{}')
            if isinstance(body_raw, str):
                body_raw = json.loads(body_raw)
            if body_raw['detail']:
                dynamodb_metadata = body_raw.get('detail', {}).get('dynamodb', {}).get('NewImage', {})
            else:
                dynamodb_metadata = body_raw

            vdsc_metadata = VdscMetadataDTO.from_dynamodb_item(dynamodb_metadata)
            _process_video_event(vdsc_metadata)

        except Exception as e:
            logger.error(f"Erro ao processar eventos do DynamoDB: {e}", exc_info=True)
            return {'statusCode': 500, 'body': json.dumps({"error": str(e)})}

    return {'statusCode': 202, 'body': json.dumps({"status": f"Recebido {len(records)} evento(s) para processamento."})}

def _process_video_event(vdsc_metadata):

    try:
        logger.info(f"Processando vídeo ID: {vdsc_metadata.video_id}")
        controller.video_slice_processing(vdsc_metadata, config)
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
    temp_path = '/tmp'
    if os.path.isdir(temp_path):
        for filename in os.listdir(temp_path):
            file_path = os.path.join(temp_path, filename)
            try:
                logger.info(f"Removendo {file_path}")
                if os.path.isfile(file_path): os.unlink(file_path)
                elif os.path.isdir(file_path): shutil.rmtree(file_path)
            except Exception as e:
                logger.warning(f"Não foi possível remover {file_path}: {e}")
    else:
        logger.warning(f"O diretório temporário {temp_path} não existe.")

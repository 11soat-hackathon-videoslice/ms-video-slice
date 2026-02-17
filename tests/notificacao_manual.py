import sys
import os
import json
from pathlib import Path

# Adicionar path para o diretório src do ms-video-slice
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Adicionar path para o diretório src do video-slice-core
core_src_path = Path(__file__).parent.parent.parent / "video-slice-core" / "src"
sys.path.insert(0, str(core_src_path))

from core.utils import get_event_schedule_timestamp
from core.dtos import VdscMetadataDTO
from aws.config import SliceVdscConfig
from aws.datasources.producer import EventProducer
from core.utils.slice_process_util import create_notification
from core.enums import NotificationChannelsEnum
from core.dtos import NotificationDto
from core.enums.email_template_enum import EmailTemplateEnum


# ============================================================
# Teste Producer
# ============================================================
def notificacao_manual():
    # Caminho do arquivo JSON com o evento do DynamoDB
    json_file_path = os.path.join(os.path.dirname(__file__), '..', 'events', 'dynamodb_item_example.json')
    config = SliceVdscConfig()
    # Ler o conteúdo do arquivo JSON
    print(f"Carregando evento do arquivo: {json_file_path}")
    with open(json_file_path, 'r', encoding='utf-8') as file:
        event = json.load(file)


    producer = EventProducer()
    metadata = VdscMetadataDTO.from_dynamodb_item(event)
    log_message = f"Enviando notificação manual para EventBridge com os seguintes dados: {metadata}"
    channels = [ NotificationChannelsEnum.EMAIL.value, NotificationChannelsEnum.WEB.value ]
    notification = create_notification(metadata, channels, web_message=log_message, email_template=EmailTemplateEnum.PROCESSING)
    notification_dto = NotificationDto.from_domain(notification)
    producer.send_notification(notification_dto)

if __name__ == "__main__":

    notificacao_manual()

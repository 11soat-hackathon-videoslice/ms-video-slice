import sys
import os
import json

from core.utils import get_event_schedule_timestamp
from src import VdscMetadataDTO, VdscConfig, EventProducer

# Adicionar path (se necessário)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ============================================================
# Teste Producer
# ============================================================
def schueduler_manual():
    # Caminho do arquivo JSON com o evento do DynamoDB
    json_file_path = os.path.join(os.path.dirname(__file__), '..', 'events', 'dynamodb_item_exemple.json')
    config = VdscConfig()
    # Ler o conteúdo do arquivo JSON
    print(f"Carregando evento do arquivo: {json_file_path}")
    with open(json_file_path, 'r', encoding='utf-8') as file:
        event = json.load(file)

    metadata = VdscMetadataDTO.from_dynamodb_item(event)
    print(f"Evento carregado: {metadata}")

    producer = EventProducer()
    schedule_timestamp = get_event_schedule_timestamp(metadata, retry_backoff_factor = 1)
    producer.send_schedule_retry_event(metadata.to_dynamodb_item(), schedule_timestamp, config.vdsc['schedule_event_rules'])

if __name__ == "__main__":


    schueduler_manual()

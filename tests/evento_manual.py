import sys
import os
import json
import boto3
from pathlib import Path


# Adicionar path para o diretório src do ms-video-slice
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Adicionar path para o diretório src do video-slice-core
core_src_path = Path(__file__).parent.parent.parent / "video-slice-core" / "src"
sys.path.insert(0, str(core_src_path))

# ============================================================
# EXEMPLO 1: Atualizar Metadados Completos
# ============================================================
def exemplo_atualizacao_completa():
    """Exemplo de atualização completa de metadados no formato DynamoDB"""
    from app import lambda_handler

    local_path = r'C:\Users\titop\OneDrive\Videos\ml9jexx5TWrC.mp4'
    s3 = boto3.client('s3')
    bucket_name = 'vdsc-prd-s3-videos'
    object_key = 'uploads/ml9jexx5TWrC.mp4'
    s3.upload_file(local_path, bucket_name, object_key)


    # Caminho do arquivo JSON com o evento do DynamoDB
    json_file_path = os.path.join(os.path.dirname(__file__), '..', 'events', 'sqs_insert_event.json')

    # Ler o conteúdo do arquivo JSON
    print(f"Carregando evento do arquivo: {json_file_path}")
    with open(json_file_path, 'r', encoding='utf-8') as file:
        event = json.load(file)

    print("Evento carregado com sucesso!")
    print(f"Número de registros: {len(event.get('Records', []))}")

    # Simular contexto Lambda (pode ser None ou um objeto mock)
    context = None

    # Chamar o handler com o evento
    print(f"\n{'='*60}")
    print("Iniciando processamento do evento...")
    print(f"{'='*60}\n")

    try:
        result = lambda_handler(event, context)
        print(f"\n{'='*60}")
        print("Processamento finalizado com sucesso!")
        print("="*60)
        if result:
            print(f"Resultado: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"Erro ao processar: {e}")
        print("="*60)
        raise


if __name__ == "__main__":
    print("="*60)
    print("TESTE DO VDSC PROCESS HANDLER")
    print(f"{'='*60}\n")

    exemplo_atualizacao_completa()

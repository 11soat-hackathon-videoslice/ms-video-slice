import sys
import os
import json



# Adicionar path (se necessário)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ============================================================
# EXEMPLO 1: Atualizar Metadados Completos
# ============================================================
def exemplo_atualizacao_completa():
    """Exemplo de atualização completa de metadados no formato DynamoDB"""

    os.system('aws s3 mv s3://vdsc-prd-s3-videos/processing/mkx8zj81Eq9o.mp4 s3://vdsc-prd-s3-videos/uploads/mkx8zj81Eq9o.mp4')

    from lambda_handler import lambda_handler

    # Caminho do arquivo JSON com o evento do DynamoDB
    json_file_path = os.path.join(os.path.dirname(__file__), '..', 'events', 'dynamodb_insert.json')

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

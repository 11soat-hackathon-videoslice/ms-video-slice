import json, os, queue, threading, requests

from concurrent.futures import ThreadPoolExecutor
from aws_lambda_powertools import Logger
from aws.datasources.database.dynamodb_repository import DynamoDBRepository
from aws.datasources.storage.s3_repository import S3StorageRepository
from aws.datasources.producer.event_producer import EventProducer
from aws.dataproxy.vdsc_dataproxy import VdscDataProxy

from core.adapters.vdsc_controller import VdscController
from aws.handler.vdsc_exception_handler import VdscExceptionHandler

logger = Logger()
# Ver instanciamentos na parte inferior do arquivo

class VdscConfig:
    _instance = None

    #Varilável de ambiente VDSC_QUALITY esperada no formato JSON, ex: '{"ultra": 1080, "high": 720, "medium": 480, "low": 360}'
    quality = json.loads(os.getenv('VDSC_QUALITY', '{"ultra": 1080, "high": 720, "medium": 480, "low": 360}').replace('\\', ''))

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VdscConfig, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self, quality=quality):
        self.aws = {
            'region': os.getenv('AWS_REGION', 'us-east-1'),
            'account_id': os.getenv('AWS_ACCOUNT_ID')}
        self.s3_bucket = {
            'name': os.getenv('S3_BUCKET_NAME', 'vdsc-prd-s3-videos'),
            'dir_uploads': os.getenv('S3_BUCKET_DIR_UPLOADS', 'uploads/'),
            'dir_finished': os.getenv('S3_BUCKET_DIR_FINISHED', 'finished/'),
            'dir_processing': os.getenv('S3_BUCKET_DIR_PROCESSING', 'processing/')
        }
        self.sqs = {
            'url': os.getenv('SQS_URL', 'https://sqs.us-east-1.amazonaws.com'),
            'dlq_name': os.getenv('SQS_DLQ_NAME', 'vdsc-prd-dlq')
        }
        self.eventbus = {
            'name': os.getenv('EVENT_BUS_NAME', 'vdsc-prd-event-bus')
        }
        self.dynamodb = {
            'table_name': os.getenv('DYNAMODB_TABLE_NAME', 'VideoSlice')
        }
        self.vdsc = {
            'max_workers': int(os.getenv('VDSC_MAX_WORKERS', '5')),
            'max_timeout': int(os.getenv('VDSC_MAX_TIMEOUT', '300')),
            'png_compression_level': int(os.getenv('VDSC_PNG_COMPRESSION_LEVEL', '9')),
            'zip_compression_level': int(os.getenv('VDSC_ZIP_COMPRESSION_LEVEL', '5')),
            'quality':quality
        }

def init_lambda_extension():
    # Se não estiver na AWS, ignora o registro da extensão
    if not os.environ.get('AWS_LAMBDA_RUNTIME_API'):
        logger.info("Ambiente local detectado. Extensão Lambda não será iniciada.")
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


def process_async_loop(ext_id):
    """Loop da extensão que mantém a Lambda viva até processar a fila"""
    while True:
        requests.get(f"http://{os.environ['AWS_LAMBDA_RUNTIME_API']}/2020-01-01/extension/event/next",headers={'Lambda-Extension-Identifier': ext_id},
            timeout=None
        )
        try:
            # Processa o que está na fila antes de liberar o congelamento
            while not async_events_queue.empty():
                task_func, data = async_events_queue.get_nowait()
                task_func(data)
                async_events_queue.task_done()
        except Exception as e:
            logger.error(f"Erro no background: {e}")



# Configurações e repositórios
config = VdscConfig()

dynamodb_repository = DynamoDBRepository(config.dynamodb['table_name'], config.aws['region'])
s3_repository = S3StorageRepository(config.s3_bucket['name'], config.aws['region'])
event_producer = EventProducer()
vdsc_handler = VdscExceptionHandler()
async_events_queue = queue.Queue()


# DataProxy e Controller globais (garante passagem pela camada Controller)
dataproxy = VdscDataProxy(dynamodb=dynamodb_repository, s3=s3_repository, event_producer=event_producer)
controller = VdscController(dataproxy=dataproxy, handler=vdsc_handler)

# Configuração do executor de threads para processamento paralelo
executor = ThreadPoolExecutor(max_workers=config.vdsc['max_workers'])
max_timeout = config.vdsc['max_timeout']



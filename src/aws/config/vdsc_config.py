import json, os

from aws.datasources.database.dynamodb_repository import DynamoDBRepository
from aws.datasources.storage.s3_repository import S3StorageRepository
from aws.datasources.producer.event_producer import EventProducer
from aws.dataproxy.vdsc_dataproxy import VdscDataProxy

from core.adapters.vdsc_controller import VdscController
from aws.handler.vdsc_exception_handler import VdscExceptionHandler

class VdscConfig:
    _instance = None

    #Varilável de ambiente VDSC_QUALITY esperada no formato JSON, ex: '{"ultra": 1080, "high": 720, "medium": 480, "low": 360}'
    quality = json.loads(os.getenv('VDSC_QUALITY', '{"ultra": 1080, "high": 720, "medium": 480, "low": 360}').replace('\\', ''))
    schedule_event_rules = {
        'retry_backoff_factor ':  int(os.getenv('SCHEDULE_EVENT_RETRY_BACKOFF_FACTOR', '5')) # quantidade em minutos x número do retry
    }

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
            'png_compression_level': int(os.getenv('VDSC_PNG_COMPRESSION_LEVEL', '9')),
            'zip_compression_level': int(os.getenv('VDSC_ZIP_COMPRESSION_LEVEL', '5')),
            'quality':quality,
            'schedule_event_rules': self.schedule_event_rules
        }

# Configurações e repositórios
config = VdscConfig()

dynamodb_repository = DynamoDBRepository(config.dynamodb['table_name'], config.aws['region'])
s3_repository = S3StorageRepository(config.s3_bucket['name'], config.aws['region'])
event_producer = EventProducer()
vdsc_handler = VdscExceptionHandler()


# DataProxy e Controller globais (garante passagem pela camada Controller)
dataproxy = VdscDataProxy(dynamodb=dynamodb_repository, s3=s3_repository, event_producer=event_producer)
controller = VdscController(dataproxy=dataproxy, handler=vdsc_handler)


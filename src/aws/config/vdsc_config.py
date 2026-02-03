import json, os

from aws.datasources.database.dynamodb_repository import DynamoDBRepository
from aws.datasources.storage.s3_repository import S3StorageRepository
from aws.datasources.producer.event_producer import EventProducer
from aws.dataproxy.vdsc_dataproxy import VdscDataProxy

from core.adapters.vdsc_controller import VdscController
from aws.handler.vdsc_exception_handler import VdscExceptionHandler

#Varilável de ambiente VDSC_QUALITY esperada no formato JSON, ex: '{"ultra": 1080, "high": 720, "medium": 480, "low": 360}'
quality = json.loads(os.getenv('VDSC_QUALITY', '{"ultra": 1080, "high": 720, "medium": 480, "low": 360}').replace('\\', ''))
schedule_event_rules = {
    'retry_backoff_factor':  int(os.getenv('SCHEDULE_EVENT_RETRY_BACKOFF_FACTOR', '5')),
    'retry_arn': os.getenv('SCHEDULE_EVENT_ROLE_ARN', 'arn:aws:sqs:us-east-1:080145351546:vdsc-prd-sqs-video-slice'),
    'retry_role_arn': os.getenv('SCHEDULE_EVENT_ROLE_ARN', 'arn:aws:iam::080145351546:role/vdsc-prd-schduler-role'),
    'retry_dlq': os.getenv('SCHEDULE_EVENT_DLQ', 'arn:aws:sqs:us-east-1:080145351546:vdsc-prd-dlq')
}

class VdscConfig:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VdscConfig, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self, quality = quality, schedule_event_rules = schedule_event_rules):
        self.aws = {
            'aws_region': os.getenv('AWS_REGION', 'us-east-1')
        }
        self.s3_bucket = {
            'bucket_name': os.getenv('S3_BUCKET_NAME', 'vdsc-prd-s3-videos'),
            'dir_uploads': os.getenv('S3_BUCKET_DIR_UPLOADS', 'uploads/'),
            'dir_finished': os.getenv('S3_BUCKET_DIR_FINISHED', 'finished/'),
            'dir_processing': os.getenv('S3_BUCKET_DIR_PROCESSING', 'processing/')
        },
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
            'schedule_event_rules': schedule_event_rules
        }

    def to_dto(self) -> VdscConfigDTO:
        quality_obj = QualityDTO(**self.vdsc['quality'])
        schedule_obj = ScheduleRulesDTO(**self.vdsc['schedule_event_rules'])

        return VdscConfigDTO(
            aws_region=self.aws['aws_region'],
            event_bus_name=self.eventbus['name'],
            dynamodb_table_name=self.dynamodb['table_name'],
            s3_bucket=S3ConfigDTO(
                bucket_name=self.s3_bucket['bucket_name'],
                dir_uploads=self.s3_bucket['dir_uploads'],
                dir_finished=self.s3_bucket['dir_finished'],
                dir_processing=self.s3_bucket['dir_processing']
            ),
            vdsc=VdscSettingsDTO(
                png_compression_level=self.vdsc['png_compression_level'],
                zip_compression_level=self.vdsc['zip_compression_level'],
                quality=quality_obj,
                schedule_event_rules=schedule_obj
            )
        )

# Configurações e repositórios
config = VdscConfig().to_dto()

dynamodb_repository = DynamoDBRepository(config.dynamodb['table_name'], config.aws['region'])
s3_repository = S3StorageRepository(config.s3_bucket['name'], config.aws['region'])
event_producer = EventProducer()
vdsc_handler = VdscExceptionHandler()


# DataProxy e Controller globais (garante passagem pela camada Controller)
dataproxy = VdscDataProxy(dynamodb=dynamodb_repository, s3=s3_repository, event_producer=event_producer)
controller = VdscController(dataproxy=dataproxy, handler=vdsc_handler)


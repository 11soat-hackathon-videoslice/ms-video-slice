import json, os

from aws.datasources.database.dynamodb_repository import DynamoDBRepository
from aws.datasources.metrics.cloudwatch_repository import CloudWatchRepository
from aws.datasources.storage.storage_repository import StorageStorageRepository
from aws.datasources.producer.event_producer import EventProducer
from aws.dataproxy.slice_dataproxy import SliceDataProxy
from aws.handler.vdsc_exception_handler import VdscExceptionHandler

from core.adapters.slice.slice_controller import SliceController
from core.dtos import VdscConfigDTO, VdscSettingsDTO, ResizeDTO, ScheduleRulesDTO
from aws_lambda_powertools import Metrics

metrics = Metrics(namespace="VideoSliceMetrics", service="VideoSlice")


#Varilável de ambiente VDSC_RESIZE esperada no formato JSON, ex: '{"ultra": 1080, "high": 720, "medium": 480, "low": 360}'
resize = json.loads(os.getenv('VDSC_RESIZE', '{"ultra": 1080, "high": 720, "medium": 480, "low": 360}').replace('\\', ''))
schedule_event_rules = {
    'retry_backoff_factor':  int(os.getenv('SCHEDULE_EVENT_RETRY_BACKOFF_FACTOR', '5')),
    'retry_arn': os.getenv('SCHEDULE_EVENT_ROLE_ARN', 'arn:aws:sqs:us-east-1:080145351546:vdsc-prd-sqs-video-slice'),
    'retry_role_arn': os.getenv('SCHEDULE_EVENT_ROLE_ARN', 'arn:aws:iam::080145351546:role/vdsc-prd-schduler-role'),
    'retry_dlq': os.getenv('SCHEDULE_EVENT_DLQ', 'arn:aws:sqs:us-east-1:080145351546:vdsc-prd-sqs-video-slice-dlq')
}

class SliceVdscConfig:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SliceVdscConfig, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self, resize = resize, schedule_event_rules = schedule_event_rules):
        self.aws = {
            'aws_region': os.getenv('AWS_REGION', 'us-east-1')
        }
        self.s3_bucket = {
            'bucket_name': os.getenv('S3_BUCKET_NAME', 'vdsc-prd-s3-videos')
        }
        self.eventbus = {
            'name': os.getenv('EVENT_BUS_NAME', 'vdsc-prd-event-bus')
        }
        self.dynamodb = {
            'table_name': os.getenv('DYNAMODB_TABLE_NAME', 'VideoSlice')
        }
        self.vdsc = {
            'dir_uploads': os.getenv('VDSC_DIR_UPLOADS', 'uploads'),
            'dir_finished': os.getenv('VDSC_DIR_FINISHED', 'finished'),
            'dir_tmp': os.getenv('VDSC_DIR_TMP', '/tmp'),
            'max_workers': int(os.getenv('VDSC_MAX_WORKERS', '10')),
            'resize':resize,
            'schedule_event_rules': schedule_event_rules,
        }

    def to_dto(self) -> VdscConfigDTO:
        resize_obj = ResizeDTO(**self.vdsc['resize'])
        schedule_obj = ScheduleRulesDTO(**self.vdsc['schedule_event_rules'])

        return VdscConfigDTO(
            aws_region=self.aws['aws_region'],
            event_bus_name=self.eventbus['name'],
            dynamodb_table_name=self.dynamodb['table_name'],
            s3_bucket_name= self.s3_bucket['bucket_name'],
            vdsc=VdscSettingsDTO(
                dir_uploads=self.vdsc['dir_uploads'],
                dir_finished=self.vdsc['dir_finished'],
                dir_tmp=self.vdsc['dir_tmp'],
                max_workers=self.vdsc['max_workers'],
                resize=resize_obj,
                schedule_event_rules=schedule_obj,
            )
        )

# Configurações e repositórios
config = SliceVdscConfig().to_dto()

dynamodb_repository = DynamoDBRepository(config.dynamodb_table_name, config.aws_region)
s3_repository = StorageStorageRepository(config.s3_bucket_name, config.aws_region)
event_producer = EventProducer()
vdsc_handler = VdscExceptionHandler()
cloudwatch = CloudWatchRepository(metrics_provider=metrics)


# DataProxy e Controller globais (garante passagem pela camada Controller)
dataproxy = SliceDataProxy(dynamodb=dynamodb_repository, storage=s3_repository, event_producer=event_producer, cloudwatch=cloudwatch)
controller = SliceController(dataproxy=dataproxy, handler=vdsc_handler)

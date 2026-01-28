import json
import os

quality = json.loads(os.getenv('VDSC_QUALITY', '{"ultra": 1080, "high": 720, "medium": 480, "low": 360}').replace('\"', '"'))

class VdscConfig:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VdscConfig, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
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
            'quality':quality
        }


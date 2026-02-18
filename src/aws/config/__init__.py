from . import slice_config

from .slice_config import (SliceVdscConfig, cloudwatch, config, controller,
                           dataproxy, dynamodb_repository, event_producer,
                           metrics, resize, s3_repository,
                           schedule_event_rules, vdsc_handler,)

__all__ = ['SliceVdscConfig', 'cloudwatch', 'config', 'controller',
           'dataproxy', 'dynamodb_repository', 'event_producer', 'metrics',
           'resize', 's3_repository', 'schedule_event_rules', 'slice_config',
           'vdsc_handler']

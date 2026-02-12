import os
from datetime import datetime
import json
import boto3, logging

from .event_producer_interface import EventProducerInterface
from core.dtos.notification_dto import NotificationDto

logger = logging.getLogger(__name__)

class EventProducer(EventProducerInterface):

    def __init__(self) -> None:
        self._scheduler = None
        self._event_producer = None
        self._config = None

    @property
    def config(self):
        """Lazy loading da configuração VdscConfig"""
        if self._config is None:
            from aws.config.vdsc_config import VdscConfig
            self._config = VdscConfig().to_dto()
        return self._config

    @property
    def scheduler(self):
        """Lazy loading do cliente boto3 scheduler"""
        if self._scheduler is None:
            self._scheduler = boto3.client('scheduler')
        return self._scheduler

    @property
    def event_producer(self):
        """Lazy loading do cliente boto3 eventbridge"""
        """Desabilita a verificação SSL para conexões locais, como LocalStack ou AWS SAM Local"""
        ssl_verify = False
        if os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
            ssl_verify = True

        if self._event_producer is None:
            self._event_producer = boto3.client('events',verify=ssl_verify)
        return self._event_producer

    @scheduler.setter
    def scheduler(self, value):
        """Setter para permitir mock do cliente nos testes"""
        self._scheduler = value

    @event_producer.setter
    def event_producer(self, value):
        self._event_producer = value


    def send_notification(self, notification: NotificationDto) -> None:
        detail = notification.to_json()
        logger.info(f"Criando notificação para EventBridge com dados: {detail}")
        try:
            response = self.event_producer.put_events(
                Entries=[
                    {
                        'Source': 'vdsc.notification',
                        'DetailType': 'VideoSlice Notification',
                        'Detail': notification.to_json(),
                        'EventBusName': self.config.event_bus_name
                    }
                ]
            )
            if response.get('FailedEntryCount', 0) > 0:
                logger.error(f"Falha ao enviar notificação para EventBridge: {response}")
                raise Exception(f"Falha ao enviar notificação: {response['Entries']}")
            logger.info(f"Notificação enviada para EventBridge com sucesso: {response}")
        except Exception as e:
            logger.error(f"Erro ao enviar notificação para EventBridge: {str(e)}", exc_info=True)

    def send_schedule_retry_event(self, event_data, schedule_time: datetime, schedule_config: dict):
        logger.info(f"Formatando EventBridge Scheduler com dados: {event_data} e horário agendado: {schedule_time}")

        # Obtendo informações do evento
        video_id = event_data['videoId']['S']
        retries = event_data['retries']['N']
        max_retries = event_data['maxRetry']['N']

        # Configurando o agendamento
        scheduler_name = f"vdsc-{video_id}-retry-{retries}-of-{max_retries}-{schedule_time.strftime('%Y%m%dT%H%M%S')}"
        scheduler_expression = f"at({schedule_time.strftime('%Y-%m-%dT%H:%M:%S')})"

        #Propriedades do agendamento
        scheduler = {
            'Name': scheduler_name,
            'ScheduleExpression': scheduler_expression,
            'FlexibleTimeWindow': {'Mode': 'OFF'},
            'ActionAfterCompletion': 'DELETE',
            'Target': {
                'Arn': schedule_config['retry_arn'],
                'RoleArn': schedule_config['retry_role_arn'],
                'Input': json.dumps(event_data), # Convertendo o DynamoDBRecord para JSON
                'DeadLetterConfig': {
                    'Arn': schedule_config['retry_dlq']
                }
            }
        }
        self._send_schedule_event(scheduler)

    def _send_schedule_event(self, scheduler) -> None:
        try:
            logger.info(f"Criando evento agendado no EventBridge Scheduler: {scheduler}")
            response = self.scheduler.create_schedule(**scheduler)
            logger.info(f"Evento agendado criado com sucesso: {response}")
        except Exception as e:
            logger.error(f"Erro ao criar evento agendado: {str(e)}", exc_info=True)
            raise


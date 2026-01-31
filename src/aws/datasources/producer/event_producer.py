from datetime import datetime
import json
import boto3, logging

from .event_producer_interface import EventProducerInterface

logger = logging.getLogger(__name__)

class EventProducer(EventProducerInterface):

    def __init__(self) -> None:
        self.scheduler = boto3.client('scheduler')

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

    def send_notification(self, event_data: dict, channels: list[str], mensagem) -> None:
        pass

    def _send_schedule_event(self, scheduler) -> None:
        try:
            logger.info(f"Criando evento agendado no EventBridge Scheduler: {scheduler}")
            response = self.scheduler.create_schedule(**scheduler)
            logger.info(f"Evento agendado criado com sucesso: {response}")
        except Exception as e:
            logger.error(f"Erro ao criar evento agendado: {str(e)}", exc_info=True)
            raise


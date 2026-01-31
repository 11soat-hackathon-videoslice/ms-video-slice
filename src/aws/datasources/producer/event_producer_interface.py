import datetime
from abc import ABC, abstractmethod

class EventProducerInterface(ABC):

    @abstractmethod
    def send_schedule_retry_event(self, event_data, schedule_time: datetime, schedule_config: dict):
        pass

    @abstractmethod
    def send_notification(self, event_data: dict, channel: str, mensagem ) -> None:
        pass

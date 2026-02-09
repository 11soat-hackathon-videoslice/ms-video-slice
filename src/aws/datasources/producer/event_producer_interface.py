import datetime
from abc import ABC, abstractmethod
from core.dtos import NotificationDto

class EventProducerInterface(ABC):

    @abstractmethod
    def send_schedule_retry_event(self, event_data, schedule_time: datetime, schedule_config: dict):
        pass

    @abstractmethod
    def send_notification(self, notification: NotificationDto ) -> None:
        pass

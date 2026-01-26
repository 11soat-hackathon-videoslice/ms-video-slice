from abc import ABC, abstractmethod

class EventProducerInterface(ABC):

    @abstractmethod
    def send_event(self, event_data: dict) -> None:
        pass

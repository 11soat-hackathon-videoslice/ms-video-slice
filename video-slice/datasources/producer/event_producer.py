from .event_producer_interface import EventProducerInterface

class EventProducer(EventProducerInterface):

    def send_event(self, event_data: dict) -> None:
        pass
from abc import ABC, abstractmethod

class CloudWatchInterface(ABC):

    @abstractmethod
    def send_metric(self, metric_info: str) -> None:
        pass
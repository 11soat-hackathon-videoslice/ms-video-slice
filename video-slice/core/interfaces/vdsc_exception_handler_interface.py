from abc import ABC, abstractmethod
from typing import Callable

class VdscExceptionHandlerInterface(ABC):

    @abstractmethod
    def vdsc_exception_handler(self, func: Callable) -> Callable:
        pass
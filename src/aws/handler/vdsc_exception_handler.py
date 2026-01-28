import logging
from functools import wraps
from typing import Callable

from ...core.exceptions.vdsc_exceptions import VdscException
from ...core.interfaces.vdsc_exception_handler_interface import VdscExceptionHandlerInterface


logger = logging.getLogger(__name__)


class VdscExceptionHandler(VdscExceptionHandlerInterface):
    """Handler para tratamento de exceções e gerenciamento de erros no processamento de vídeos"""

    def vdsc_exception_handler(self, func: Callable) -> Callable:
        """Decorador que captura VdscException e imprime a mensagem de erro"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except VdscException as e:
                error_message = f"Erro capturado: {e.message}"
                print(error_message)
                logger.error(error_message)
                raise
            except Exception as e:
                error_message = f"Erro inesperado: {str(e)}"
                print(error_message)
                logger.error(error_message)
                raise
        return wrapper

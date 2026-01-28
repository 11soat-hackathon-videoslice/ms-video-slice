"""Testes unitários para VdscExceptionHandler"""
import pytest
from unittest.mock import Mock, patch
from src.aws.handler.vdsc_exception_handler import VdscExceptionHandler
from src.core.exceptions.vdsc_exceptions import VdscException


@pytest.mark.unit
class TestVdscExceptionHandler:
    """Testes para o handler de exceções"""

    @pytest.fixture
    def handler(self):
        """Fixture para criar instância do handler"""
        return VdscExceptionHandler()

    def test_decorator_success(self, handler):
        """Testa decorador com função que executa com sucesso"""
        @handler.vdsc_exception_handler
        def successful_function():
            return "success"

        result = successful_function()
        assert result == "success"

    def test_decorator_catches_vdsc_exception(self, handler):
        """Testa decorador capturando VdscException"""
        @handler.vdsc_exception_handler
        def function_with_vdsc_exception():
            raise VdscException("Erro teste", "ERROR", {"video_id": "123"})

        with pytest.raises(VdscException):
            function_with_vdsc_exception()

    def test_decorator_catches_generic_exception(self, handler):
        """Testa decorador capturando exceção genérica"""
        @handler.vdsc_exception_handler
        def function_with_generic_exception():
            raise ValueError("Erro genérico")

        with pytest.raises(ValueError):
            function_with_generic_exception()

    @patch('builtins.print')
    def test_decorator_prints_vdsc_exception_message(self, mock_print, handler):
        """Testa se mensagem de VdscException é impressa"""
        @handler.vdsc_exception_handler
        def function_with_vdsc_exception():
            raise VdscException("Erro teste", "ERROR", {"video_id": "123"})

        with pytest.raises(VdscException):
            function_with_vdsc_exception()

        mock_print.assert_called_once()
        args = mock_print.call_args[0][0]
        assert "Erro inesperado" in args

    @patch('builtins.print')
    def test_decorator_prints_generic_exception_message(self, mock_print, handler):
        """Testa se mensagem de exceção genérica é impressa"""
        @handler.vdsc_exception_handler
        def function_with_generic_exception():
            raise ValueError("Erro genérico")

        with pytest.raises(ValueError):
            function_with_generic_exception()

        mock_print.assert_called_once()
        args = mock_print.call_args[0][0]
        assert "Erro inesperado" in args

    def test_decorator_preserves_function_metadata(self, handler):
        """Testa se o decorador preserva os metadados da função"""
        @handler.vdsc_exception_handler
        def test_function():
            """Docstring de teste"""
            pass

        assert test_function.__name__ == "test_function"
        assert test_function.__doc__ == "Docstring de teste"

    def test_decorator_with_function_arguments(self, handler):
        """Testa decorador com função que recebe argumentos"""
        @handler.vdsc_exception_handler
        def function_with_args(a, b):
            return a + b

        result = function_with_args(3, 5)
        assert result == 8

    def test_decorator_with_keyword_arguments(self, handler):
        """Testa decorador com função que recebe kwargs"""
        @handler.vdsc_exception_handler
        def function_with_kwargs(name, age=25):
            return f"{name} tem {age} anos"

        result = function_with_kwargs(name="João", age=30)
        assert result == "João tem 30 anos"

    @patch('src.aws.handler.vdsc_exception_handler.logger')
    def test_decorator_logs_vdsc_exception(self, mock_logger, handler):
        """Testa se VdscException é registrada no logger"""
        @handler.vdsc_exception_handler
        def function_with_error():
            raise VdscException("Erro de teste", "ERROR", {})

        with pytest.raises(VdscException):
            function_with_error()

        mock_logger.error.assert_called_once()

    @patch('src.aws.handler.vdsc_exception_handler.logger')
    def test_decorator_logs_generic_exception(self, mock_logger, handler):
        """Testa se exceção genérica é registrada no logger"""
        @handler.vdsc_exception_handler
        def function_with_error():
            raise RuntimeError("Erro de runtime")

        with pytest.raises(RuntimeError):
            function_with_error()

        mock_logger.error.assert_called_once()

    def test_decorator_with_vdsc_exception_metadata(self, handler):
        """Testa VdscException com metadados"""
        metadata = {'videoId': 'video456', 'status': 'FAILED'}

        @handler.vdsc_exception_handler
        def function_with_metadata():
            raise VdscException("Erro com metadados", "ERROR", metadata)

        with pytest.raises(VdscException) as exc_info:
            function_with_metadata()

        assert exc_info.value.message == "Erro com metadados"
        assert exc_info.value.metadata == metadata

    def test_decorator_reraises_exception(self, handler):
        """Testa se decorador re-lança a exceção"""
        @handler.vdsc_exception_handler
        def function_raises():
            raise KeyError("Chave não encontrada")

        with pytest.raises(KeyError, match="Chave não encontrada"):
            function_raises()

    def test_decorator_with_none_return(self, handler):
        """Testa função decorada que retorna None"""
        @handler.vdsc_exception_handler
        def function_returns_none():
            return None

        result = function_returns_none()
        assert result is None

    def test_decorator_with_complex_return(self, handler):
        """Testa função decorada que retorna estrutura complexa"""
        @handler.vdsc_exception_handler
        def function_returns_dict():
            return {
                'status': 'success',
                'data': {'items': [1, 2, 3]},
                'count': 3
            }

        result = function_returns_dict()
        assert result['status'] == 'success'
        assert len(result['data']['items']) == 3

    @patch('builtins.print')
    def test_vdsc_exception_message_format(self, mock_print, handler):
        """Testa formato da mensagem de VdscException"""
        @handler.vdsc_exception_handler
        def func():
            raise VdscException("Mensagem de erro específica", "ERROR", {})

        with pytest.raises(VdscException):
            func()

        call_args = mock_print.call_args[0][0]
        assert "Erro inesperado" in call_args
        assert "Mensagem de erro específica" in call_args

    @patch('builtins.print')
    def test_generic_exception_message_format(self, mock_print, handler):
        """Testa formato da mensagem de exceção genérica"""
        @handler.vdsc_exception_handler
        def func():
            raise TypeError("Tipo incorreto")

        with pytest.raises(TypeError):
            func()

        call_args = mock_print.call_args[0][0]
        assert "Erro inesperado:" in call_args
        assert "Tipo incorreto" in call_args


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
        assert "Erro capturado" in args

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

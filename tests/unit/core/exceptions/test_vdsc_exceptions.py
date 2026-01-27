"""Testes unitários para VdscException"""
import pytest
from src.core.exceptions.vdsc_exceptions import VdscException


@pytest.mark.unit
class TestVdscException:
    """Testes para a exceção customizada VdscException"""

    def test_create_exception(self):
        """Testa criação de exceção"""
        exception = VdscException(
            message="Erro de teste",
            info="INFO",
            metadata={"video_id": "123"}
        )
        assert exception.message == "Erro de teste"
        assert exception.info == "INFO"
        assert exception.metadata == {"video_id": "123"}

    def test_exception_str_representation(self):
        """Testa representação string da exceção"""
        exception = VdscException(
            message="Erro de teste",
            info="ERROR",
            metadata={"video_id": "123", "status": "failed"}
        )
        str_repr = str(exception)
        assert "VdscException" in str_repr
        assert "Erro de teste" in str_repr
        assert "ERROR" in str_repr
        assert "video_id" in str_repr

    def test_raise_exception(self):
        """Testa levantamento de exceção"""
        with pytest.raises(VdscException) as exc_info:
            raise VdscException(
                message="Teste de erro",
                info="TEST",
                metadata={}
            )
        assert exc_info.value.message == "Teste de erro"
        assert exc_info.value.info == "TEST"

    def test_exception_with_empty_metadata(self):
        """Testa exceção com metadata vazio"""
        exception = VdscException(
            message="Erro",
            info="INFO",
            metadata={}
        )
        assert exception.metadata == {}

    def test_exception_inheritance(self):
        """Testa que VdscException herda de Exception"""
        exception = VdscException("Erro", "INFO", {})
        assert isinstance(exception, Exception)

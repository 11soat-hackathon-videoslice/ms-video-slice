"""Testes unitários para VdscStatusEnum"""
import pytest
from src.core.enums.vdsc_status_enum import VdscStatusEnum


@pytest.mark.unit
class TestVdscStatusEnum:
    """Testes para a enumeração de status"""

    def test_enum_values(self):
        """Testa se todos os valores do enum estão definidos corretamente"""
        assert VdscStatusEnum.UPLOADED.value == "UPLOADED"
        assert VdscStatusEnum.PROCESSING.value == "PROCESSING"
        assert VdscStatusEnum.FINISHED.value == "FINISHED"
        assert VdscStatusEnum.RETRYING.value == "RETRYING"
        assert VdscStatusEnum.FAILED.value == "FAILED"
        assert VdscStatusEnum.ERROR.value == "ERROR"

    def test_is_valid_with_valid_status(self):
        """Testa validação com status válido"""
        assert VdscStatusEnum.is_valid("UPLOADED") is True
        assert VdscStatusEnum.is_valid("PROCESSING") is True
        assert VdscStatusEnum.is_valid("FINISHED") is True

    def test_is_valid_with_invalid_status(self):
        """Testa validação com status inválido"""
        assert VdscStatusEnum.is_valid("INVALID") is False
        assert VdscStatusEnum.is_valid("") is False
        assert VdscStatusEnum.is_valid("uploaded") is False

    def test_get_all_values(self):
        """Testa obtenção de todos os valores"""
        all_values = VdscStatusEnum.get_all_values()
        assert len(all_values) == 6
        assert "UPLOADED" in all_values
        assert "PROCESSING" in all_values
        assert "FINISHED" in all_values
        assert "RETRYING" in all_values
        assert "FAILED" in all_values
        assert "ERROR" in all_values

    def test_str_method(self):
        """Testa método __str__ do enum"""
        assert str(VdscStatusEnum.UPLOADED) == "UPLOADED"
        assert str(VdscStatusEnum.PROCESSING) == "PROCESSING"

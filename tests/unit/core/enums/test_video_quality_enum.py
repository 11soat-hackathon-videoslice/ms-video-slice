"""Testes unitários para VideoQuality enum"""
import pytest
from src.core.enums.video_quality_enum import VideoQuality


@pytest.mark.unit
class TestVideoQuality:
    """Testes para a enumeração de qualidade de vídeo"""

    def test_enum_values(self):
        """Testa se todos os valores do enum estão definidos corretamente"""
        assert VideoQuality.ULTRA.value == "ultra"
        assert VideoQuality.HIGH.value == "high"
        assert VideoQuality.MEDIUM.value == "medium"
        assert VideoQuality.LOW.value == "low"

    def test_is_valid_with_valid_quality(self):
        """Testa validação com qualidade válida"""
        assert VideoQuality.is_valid("ultra") is True
        assert VideoQuality.is_valid("high") is True
        assert VideoQuality.is_valid("medium") is True
        assert VideoQuality.is_valid("low") is True

    def test_is_valid_with_invalid_quality(self):
        """Testa validação com qualidade inválida"""
        assert VideoQuality.is_valid("invalid") is False
        assert VideoQuality.is_valid("") is False
        assert VideoQuality.is_valid("HIGH") is False

    def test_get_all_values(self):
        """Testa obtenção de todos os valores"""
        all_values = VideoQuality.get_all_values()
        assert len(all_values) == 4
        assert "ultra" in all_values
        assert "high" in all_values
        assert "medium" in all_values
        assert "low" in all_values

    def test_str_method(self):
        """Testa método __str__ do enum"""
        assert str(VideoQuality.ULTRA) == "ultra"
        assert str(VideoQuality.HIGH) == "high"

    def test_get_scale_factor(self):
        """Testa obtenção de fator de escala"""
        assert VideoQuality.ULTRA.get_scale_factor() == "ultra"
        assert VideoQuality.HIGH.get_scale_factor() == "high"
        assert VideoQuality.MEDIUM.get_scale_factor() == "medium"
        assert VideoQuality.LOW.get_scale_factor() == "low"

    def test_from_scale_valid(self):
        """Testa criação a partir de escala válida"""
        assert VideoQuality.from_scale("ultra") == VideoQuality.ULTRA
        assert VideoQuality.from_scale("high") == VideoQuality.HIGH
        assert VideoQuality.from_scale("medium") == VideoQuality.MEDIUM
        assert VideoQuality.from_scale("low") == VideoQuality.LOW

    def test_from_scale_invalid(self):
        """Testa criação a partir de escala inválida"""
        with pytest.raises(ValueError):
            VideoQuality.from_scale("invalid")

"""Testes unitários para StorageInterface"""
import pytest
from aws.datasources.storage.storage_interface import StorageInterface


@pytest.mark.unit
class TestStorageInterface:
    """Testes para a interface StorageInterface"""

    def test_interface_is_abstract(self):
        """Testa que a interface é abstrata e não pode ser instanciada"""
        with pytest.raises(TypeError):
            StorageInterface()

    def test_interface_has_required_methods(self):
        """Testa que a interface tem todos os métodos necessários"""
        required_methods = [
            'delete_file',
            'delete_temp_files',
            'open_file',
            'upload_finished_zip',
            'save_file'
        ]

        for method in required_methods:
            assert hasattr(StorageInterface, method)

    def test_concrete_implementation(self):
        """Testa implementação concreta da interface"""

        class ConcreteStorage(StorageInterface):
            def delete_file(self, file_path: str) -> None:
                pass

            def delete_temp_files(self, dir_tmp: str) -> None:
                pass

            def open_file(self, file_path: str) -> bytes:
                return b"test_data"

            def upload_finished_zip(self, output_directory: str, target_path: str) -> None:
                pass

            def save_file(self, file_path: str, data: bytes) -> None:
                pass

        storage = ConcreteStorage()

        # Testa open_file
        result = storage.open_file("test_path")
        assert result == b"test_data"

        # Testa que outros métodos podem ser chamados sem erro
        storage.delete_file("test_path")
        storage.delete_temp_files("/tmp/test")
        storage.upload_finished_zip("output/", "target.zip")
        storage.save_file("test.txt", b"data")

    def test_concrete_implementation_missing_method(self):
        """Testa que implementação incompleta falha"""

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            class IncompleteStorage(StorageInterface):
                def delete_file(self, file_path: str) -> None:
                    pass
                # Faltando outros métodos

            IncompleteStorage()

    def test_method_signatures(self):
        """Testa que os métodos abstratos têm as assinaturas corretas"""

        class ConcreteStorage(StorageInterface):
            def delete_file(self, file_path: str) -> None:
                assert isinstance(file_path, str)

            def delete_temp_files(self, dir_tmp: str) -> None:
                assert isinstance(dir_tmp, str)

            def open_file(self, file_path: str) -> bytes:
                assert isinstance(file_path, str)
                return b""

            def upload_finished_zip(self, output_directory: str, target_path: str) -> None:
                assert isinstance(output_directory, str)
                assert isinstance(target_path, str)

            def save_file(self, file_path: str, data: bytes) -> None:
                assert isinstance(file_path, str)
                assert isinstance(data, bytes)

        storage = ConcreteStorage()

        # Testa tipos dos parâmetros
        storage.delete_file("path")
        storage.delete_temp_files("/tmp")
        result = storage.open_file("path")
        assert isinstance(result, bytes)
        storage.upload_finished_zip("output", "target")
        storage.save_file("file", b"data")

    def test_multiple_implementations(self):
        """Testa que múltiplas implementações podem coexistir"""

        class StorageA(StorageInterface):
            def delete_file(self, file_path: str) -> None:
                pass
            def delete_temp_files(self, dir_tmp: str) -> None:
                pass
            def open_file(self, file_path: str) -> bytes:
                return b"A"
            def upload_finished_zip(self, output_directory: str, target_path: str) -> None:
                pass
            def save_file(self, file_path: str, data: bytes) -> None:
                pass

        class StorageB(StorageInterface):
            def delete_file(self, file_path: str) -> None:
                pass
            def delete_temp_files(self, dir_tmp: str) -> None:
                pass
            def open_file(self, file_path: str) -> bytes:
                return b"B"
            def upload_finished_zip(self, output_directory: str, target_path: str) -> None:
                pass
            def save_file(self, file_path: str, data: bytes) -> None:
                pass

        storage_a = StorageA()
        storage_b = StorageB()

        assert storage_a.open_file("test") == b"A"
        assert storage_b.open_file("test") == b"B"


from abc import ABC, abstractmethod

class StorageInterface(ABC):

    @abstractmethod
    def create_zip_file(self, directory_path: str, zip_file_path: str) -> None:
        pass

    @abstractmethod
    def delete_file(self, file_path: str) -> None:
        pass

    @abstractmethod
    def delete_temp_files(self, dir_tmp:str) -> None:
        pass

    @abstractmethod
    def open_file(self, file_path: str) -> bytes:
        pass

    @abstractmethod
    def save_file(self, file_path: str, data: bytes) -> None:
        pass

    @abstractmethod
    def upload_file(self, source_path: str, target_path: str) -> None:
        pass



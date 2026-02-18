from abc import ABC, abstractmethod

class StorageInterface(ABC):

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
    def upload_finished_zip(self, output_directory: str, target_path: str) -> None:
        pass

    @abstractmethod
    def save_file(self, file_path: str, data: bytes) -> None:
        pass





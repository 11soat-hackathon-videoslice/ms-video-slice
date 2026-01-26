class VdscException(Exception):
    def __init__(self, message: str, info: str, metadata: dict):
        super().__init__(message)
        self.message = message
        self.info = info
        self.metadata = metadata

    def __str__(self):
        return f"VdscException: {self.message} | Info: {self.info} | Metadata: {self.metadata}"




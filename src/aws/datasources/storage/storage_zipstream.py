class StorageZipStreamReader:
    def __init__(self, zip_stream):
        self._iter = iter(zip_stream)

    def read(self, _size=-1):
        return next(self._iter, b"")
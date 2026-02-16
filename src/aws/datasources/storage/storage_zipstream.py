class StorageZipStreamReader:
    def __init__(self, zip_stream):
        self._iter = iter(zip_stream)
        self._buffer = b""

    def read(self, size=-1):
        if size < 0:
            self._buffer += b"".join(self._iter)
            res, self._buffer = self._buffer, b""
            return res

        while len(self._buffer) < size:
            try:
                self._buffer += next(self._iter)
            except StopIteration:
                break

        res, self._buffer = self._buffer[:size], self._buffer[size:]
        return res

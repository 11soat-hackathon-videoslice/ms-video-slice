"""Testes unitários para StorageZipStreamReader"""
import pytest
from aws.datasources.storage.storage_zipstream import StorageZipStreamReader


@pytest.mark.unit
class TestStorageZipStreamReader:
    """Testes para a classe StorageZipStreamReader"""

    def test_init(self):
        """Testa inicialização da classe"""
        zip_stream = [b"chunk1", b"chunk2"]
        reader = StorageZipStreamReader(zip_stream)

        assert reader._buffer == b""
        assert reader._iter is not None

    def test_read_with_negative_size(self):
        """Testa leitura de todo o conteúdo com size=-1"""
        zip_stream = [b"chunk1", b"chunk2", b"chunk3"]
        reader = StorageZipStreamReader(zip_stream)

        result = reader.read(-1)

        assert result == b"chunk1chunk2chunk3"
        assert reader._buffer == b""

    def test_read_with_zero_size(self):
        """Testa leitura com size=0"""
        zip_stream = [b"chunk1", b"chunk2"]
        reader = StorageZipStreamReader(zip_stream)

        result = reader.read(0)

        assert result == b""
        assert reader._buffer == b""

    def test_read_exact_size(self):
        """Testa leitura de tamanho exato disponível no buffer"""
        zip_stream = [b"12345", b"67890"]
        reader = StorageZipStreamReader(zip_stream)

        result = reader.read(5)

        assert result == b"12345"
        assert reader._buffer == b""

    def test_read_smaller_than_chunk(self):
        """Testa leitura de tamanho menor que um chunk"""
        zip_stream = [b"1234567890"]
        reader = StorageZipStreamReader(zip_stream)

        result = reader.read(5)

        assert result == b"12345"
        assert reader._buffer == b"67890"

    def test_read_larger_than_single_chunk(self):
        """Testa leitura de tamanho maior que um único chunk"""
        zip_stream = [b"12345", b"67890", b"ABCDE"]
        reader = StorageZipStreamReader(zip_stream)

        result = reader.read(12)

        assert result == b"1234567890AB"
        assert reader._buffer == b"CDE"

    def test_read_multiple_times(self):
        """Testa múltiplas leituras sequenciais"""
        zip_stream = [b"12345", b"67890", b"ABCDE"]
        reader = StorageZipStreamReader(zip_stream)

        result1 = reader.read(5)
        result2 = reader.read(5)
        result3 = reader.read(5)

        assert result1 == b"12345"
        assert result2 == b"67890"
        assert result3 == b"ABCDE"
        assert reader._buffer == b""

    def test_read_more_than_available(self):
        """Testa leitura de mais dados do que disponível"""
        zip_stream = [b"12345", b"67890"]
        reader = StorageZipStreamReader(zip_stream)

        result = reader.read(20)

        assert result == b"1234567890"
        assert reader._buffer == b""

    def test_read_after_exhausted(self):
        """Testa leitura após esgotar o stream"""
        zip_stream = [b"12345"]
        reader = StorageZipStreamReader(zip_stream)

        result1 = reader.read(-1)
        result2 = reader.read(10)

        assert result1 == b"12345"
        assert result2 == b""
        assert reader._buffer == b""

    def test_read_empty_stream(self):
        """Testa leitura de stream vazio"""
        zip_stream = []
        reader = StorageZipStreamReader(zip_stream)

        result = reader.read(10)

        assert result == b""
        assert reader._buffer == b""

    def test_read_with_empty_chunks(self):
        """Testa leitura com chunks vazios no meio"""
        zip_stream = [b"12345", b"", b"67890", b""]
        reader = StorageZipStreamReader(zip_stream)

        result = reader.read(10)

        assert result == b"1234567890"
        assert reader._buffer == b""

    def test_read_single_byte_at_time(self):
        """Testa leitura byte por byte"""
        zip_stream = [b"ABC"]
        reader = StorageZipStreamReader(zip_stream)

        result1 = reader.read(1)
        result2 = reader.read(1)
        result3 = reader.read(1)
        result4 = reader.read(1)

        assert result1 == b"A"
        assert result2 == b"B"
        assert result3 == b"C"
        assert result4 == b""

    def test_read_alternating_sizes(self):
        """Testa leitura alternando entre tamanhos diferentes"""
        zip_stream = [b"1234567890", b"ABCDEFGHIJ"]
        reader = StorageZipStreamReader(zip_stream)

        result1 = reader.read(3)
        result2 = reader.read(7)
        result3 = reader.read(5)
        result4 = reader.read(-1)

        assert result1 == b"123"
        assert result2 == b"4567890"
        assert result3 == b"ABCDE"
        assert result4 == b"FGHIJ"

    def test_read_with_buffer_accumulation(self):
        """Testa acumulação no buffer quando múltiplos chunks são menores que o tamanho solicitado"""
        zip_stream = [b"12", b"34", b"56", b"78"]
        reader = StorageZipStreamReader(zip_stream)

        result = reader.read(6)

        assert result == b"123456"
        # O buffer fica vazio porque acumulou exatamente 6 bytes (loop para quando len >= size)
        assert reader._buffer == b""

    def test_read_negative_size_with_buffer(self):
        """Testa leitura com size=-1 quando já há dados no buffer"""
        zip_stream = [b"67890", b"ABCDE"]
        reader = StorageZipStreamReader(zip_stream)

        # Pré-popula o buffer: lê 3 bytes do primeiro chunk
        reader.read(3)  # Retorna "678", buffer="90"

        # Lê todo o resto: buffer atual + todo o iterador
        result = reader.read(-1)

        # buffer="90" + "ABCDE" (do iterador) = "90ABCDE"
        assert result == b"90ABCDE"

    def test_read_zero_after_partial_read(self):
        """Testa leitura com size=0 após leitura parcial"""
        zip_stream = [b"1234567890"]
        reader = StorageZipStreamReader(zip_stream)

        reader.read(5)
        result = reader.read(0)

        assert result == b""
        assert reader._buffer == b"67890"

    def test_buffer_preservation_between_reads(self):
        """Testa que o buffer é preservado corretamente entre leituras"""
        zip_stream = [b"1234567890"]
        reader = StorageZipStreamReader(zip_stream)

        reader.read(3)
        assert reader._buffer == b"4567890"

        reader.read(2)
        assert reader._buffer == b"67890"

        reader.read(5)
        assert reader._buffer == b""

    def test_read_with_large_chunks(self):
        """Testa leitura com chunks grandes"""
        large_chunk = b"X" * 10000
        zip_stream = [large_chunk, large_chunk]
        reader = StorageZipStreamReader(zip_stream)

        result = reader.read(15000)

        assert len(result) == 15000
        assert result == b"X" * 15000
        assert len(reader._buffer) == 5000

    def test_read_with_generator(self):
        """Testa leitura com um generator em vez de lista"""
        def chunk_generator():
            yield b"chunk1"
            yield b"chunk2"
            yield b"chunk3"

        reader = StorageZipStreamReader(chunk_generator())

        result = reader.read(12)

        # "chunk1" = 6 bytes, "chunk2" = 6 bytes = 12 bytes total
        # Loop para quando len(buffer) >= 12, então não lê "chunk3"
        assert result == b"chunk1chunk2"
        assert reader._buffer == b""

    def test_stop_iteration_handling(self):
        """Testa tratamento correto de StopIteration"""
        zip_stream = [b"12345"]
        reader = StorageZipStreamReader(zip_stream)

        # Primeira leitura consome todo o stream
        result1 = reader.read(10)

        # Segunda leitura deve tratar StopIteration graciosamente
        result2 = reader.read(10)

        assert result1 == b"12345"
        assert result2 == b""

    def test_read_exact_buffer_size(self):
        """Testa leitura quando o tamanho solicitado é exatamente o tamanho do buffer"""
        zip_stream = [b"1234567890"]
        reader = StorageZipStreamReader(zip_stream)

        # Pré-popula o buffer
        reader.read(5)

        # Lê exatamente o tamanho do buffer restante
        result = reader.read(5)

        assert result == b"67890"
        assert reader._buffer == b""

    def test_multiple_negative_reads(self):
        """Testa múltiplas leituras com size=-1"""
        zip_stream = [b"chunk1", b"chunk2"]
        reader = StorageZipStreamReader(zip_stream)

        result1 = reader.read(-1)
        result2 = reader.read(-1)
        result3 = reader.read(-1)

        assert result1 == b"chunk1chunk2"
        assert result2 == b""
        assert result3 == b""


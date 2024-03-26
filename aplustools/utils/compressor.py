import lzma
import brotli
import json
import os
import zstandard as zstd
import py7zr
import io


class FileContainer:
    def __init__(self, compressor, block_size=1024 * 1024):  # Block size of 1 MB
        self.compressor = compressor
        self.block_size = block_size
        self.current_block = bytearray()
        self.compressed_data = bytearray()
        self.files = {}
        self.block_offsets = []

    def _compress_current_block(self):
        if self.current_block:
            compressed_block = self.compressor.compress(self.current_block)
            self.block_offsets.append({'start': len(self.compressed_data), 'length': len(compressed_block)})
            self.compressed_data.extend(compressed_block)
            self.current_block = bytearray()

    def add_file(self, filename, data):
        if len(self.current_block) + len(data) > self.block_size:
            self._compress_current_block()

        file_info = {
            'block_index': len(self.block_offsets),
            'start': len(self.current_block),
            'length': len(data)
        }
        self.current_block.extend(data)
        self.files[filename] = file_info

        if len(self.current_block) >= self.block_size:
            self._compress_current_block()

    def get_compressed_container(self):
        self._compress_current_block()  # Compress any remaining data in the current block
        index_data = json.dumps({'files': self.files, 'blocks': self.block_offsets}).encode()
        index_length = len(index_data).to_bytes(4, 'big')
        return index_length + index_data + self.compressed_data

    def extract_file(self, compressed_container, filename):
        index_length = int.from_bytes(compressed_container[:4], 'big')
        index_data = compressed_container[4:4 + index_length]
        index = json.loads(index_data)

        file_info = index['files'][filename]
        block_info = index['blocks'][file_info['block_index']]

        start_block = block_info['start']
        length_block = block_info['length']
        compressed_block = compressed_container[
                           4 + index_length + start_block:4 + index_length + start_block + length_block]

        decompressed_block = self.compressor.decompress(compressed_block)

        start_file = file_info['start']
        length_file = file_info['length']
        return decompressed_block[start_file:start_file + length_file]


class FileContainerV2:
    def __init__(self, compressor, block_size=1024 * 1024):  # Block size of 1 MB
        self.compressor = compressor
        self.block_size = block_size
        self.current_block = bytearray()
        self.compressed_data = bytearray()
        self.file_info = {}  # Stores info about files by filename
        self.index_to_name = []  # Maps numeric indexes to filenames
        self.block_offsets = []

    def _compress_current_block(self):
        if self.current_block:
            compressed_block = self.compressor.compress(self.current_block)
            self.block_offsets.append({'start': len(self.compressed_data), 'length': len(compressed_block)})
            self.compressed_data.extend(compressed_block)
            self.current_block = bytearray()

    def add_file(self, filename, data):
        if len(self.current_block) + len(data) > self.block_size:
            self._compress_current_block()

        file_index = len(self.index_to_name)
        self.index_to_name.append(filename)
        self.file_info[filename] = {
            'index': file_index,
            'block_index': len(self.block_offsets),
            'start': len(self.current_block),
            'length': len(data)
        }
        self.current_block.extend(data)

        if len(self.current_block) >= self.block_size:
            self._compress_current_block()

    def get_compressed_container(self):
        self._compress_current_block()  # Compress any remaining data in the current block
        index_data = json.dumps({'file_info': self.file_info, 'block_offsets': self.block_offsets, 'index_to_name': self.index_to_name}).encode()
        index_length = len(index_data).to_bytes(4, 'big')
        return index_length + index_data + self.compressed_data

    def extract_file(self, compressed_container, file_identifier):
        index_length = int.from_bytes(compressed_container[:4], 'big')
        index_data = compressed_container[4:4 + index_length]
        index = json.loads(index_data)

        filename = file_identifier if isinstance(file_identifier, str) else index['index_to_name'][file_identifier]
        file_info = index['file_info'][filename]
        block_info = index['block_offsets'][file_info['block_index']]

        start_block = block_info['start']
        length_block = block_info['length']
        compressed_block = compressed_container[4 + index_length + start_block:4 + index_length + start_block + length_block]

        decompressed_block = self.compressor.decompress(compressed_block)

        start_file = file_info['start']
        length_file = file_info['length']
        return decompressed_block[start_file:start_file + length_file]


class FileContainerV3:
    def __init__(self, compressor, block_size=1024 * 1024):  # Block size of 1 MB
        self.compressor = compressor
        self.block_size = block_size
        self.current_block = bytearray()
        self.compressed_data = bytearray()
        self.file_info = {}  # Stores info about files by filename
        self.index_to_name = []  # Maps numeric indexes to filenames
        self.block_offsets = []

    def _compress_current_block(self):
        if self.current_block:
            compressed_block = self.compressor.compress(self.current_block)
            self.block_offsets.append({'start': len(self.compressed_data), 'length': len(compressed_block)})
            self.compressed_data.extend(compressed_block)
            self.current_block = bytearray()

    def add_file(self, filename, data):
        if len(self.current_block) + len(data) > self.block_size:
            self._compress_current_block()

        file_index = len(self.index_to_name)
        self.index_to_name.append(filename)
        self.file_info[filename] = {
            'index': file_index,
            'block_index': len(self.block_offsets),
            'start': len(self.current_block),
            'length': len(data)
        }
        self.current_block.extend(data)

        if len(self.current_block) >= self.block_size:
            self._compress_current_block()

    def get_compressed_container(self):
        self._compress_current_block()  # Compress any remaining data in the current block
        index_data = json.dumps({'file_info': self.file_info, 'block_offsets': self.block_offsets, 'index_to_name': self.index_to_name}).encode()
        compressed_index_data = self.compressor.compress(index_data)
        index_length = len(compressed_index_data).to_bytes(4, 'big')
        return index_length + compressed_index_data + self.compressed_data

    def extract_file(self, compressed_container, file_identifier):
        compressed_index_length = int.from_bytes(compressed_container[:4], 'big')
        compressed_index_data = compressed_container[4:4 + compressed_index_length]
        index_data = self.compressor.decompress(compressed_index_data)
        index = json.loads(index_data)

        filename = file_identifier if isinstance(file_identifier, str) else index['index_to_name'][file_identifier]
        file_info = index['file_info'][filename]
        block_info = index['block_offsets'][file_info['block_index']]

        start_block = block_info['start']
        length_block = block_info['length']
        compressed_block = compressed_container[4 + compressed_index_length + start_block:4 + compressed_index_length + start_block + length_block]

        decompressed_block = self.compressor.decompress(compressed_block)

        start_file = file_info['start']
        length_file = file_info['length']
        return decompressed_block[start_file:start_file + length_file]


class ChunkCompressorBase:
    def compress(self, data_chunk):
        return data_chunk

    def decompress(self, compressed_chunk):
        return compressed_chunk


class BrotliChunkCompressor(ChunkCompressorBase):
    def __init__(self, quality=11):  # Maximum compression quality
        self.quality = quality

    def compress(self, data_chunk):
        # Compress the data chunk with Brotli
        return brotli.compress(data_chunk, quality=self.quality)

    def decompress(self, compressed_chunk):
        # Decompress the data chunk with Brotli
        return brotli.decompress(compressed_chunk)

    @staticmethod
    def add_markers(data, start_marker, end_marker):
        # Add start and end markers to the data
        return start_marker + data + end_marker


class LZMAChunkCompressor(ChunkCompressorBase):
    def __init__(self, preset=lzma.PRESET_EXTREME):
        self.preset = preset

    def compress(self, data_chunk):
        # Compress the data chunk with LZMA
        return lzma.compress(data_chunk, preset=self.preset)

    def decompress(self, compressed_chunk):
        # Decompress the data chunk with LZMA
        return lzma.decompress(compressed_chunk)


class ZstdCompressor(ChunkCompressorBase):
    def __init__(self, level=3):
        self.compressor = zstd.ZstdCompressor(level=level)
        self.decompressor = zstd.ZstdDecompressor()

    def compress(self, data_chunk):
        return self.compressor.compress(data_chunk)

    def decompress(self, compressed_chunk):
        return self.decompressor.decompress(compressed_chunk)


class LZMA2Compressor(ChunkCompressorBase):
    def compress(self, data_chunk):
        with io.BytesIO() as buffer, py7zr.SevenZipFile(buffer, 'w', filters=[{'id': py7zr.FILTER_LZMA2}]) as archive:
            # Create a file-like object from data_chunk
            file_like_data = io.BytesIO(data_chunk)
            archive.write({"data": file_like_data})
            buffer.seek(0)  # Reset buffer position to the beginning
            return buffer.getvalue()

    def decompress(self, compressed_chunk):
        with io.BytesIO(compressed_chunk) as input_buffer, py7zr.SevenZipFile(input_buffer, 'r') as archive:
            output_buffer = io.BytesIO()
            archive.extractall(path=output_buffer)
            output_buffer.seek(0)  # Reset buffer position to the beginning
            return output_buffer.read()


if __name__ == "__main__":
    compressor = BrotliChunkCompressor()
    container = FileContainerV3(compressor, block_size=2048*2048)

    image_data = {}
    for file in os.listdir("./images_htfs"):
        if file.endswith(".HTSF"):
            with open(os.path.join("./images_htfs", file), "rb") as f:
                image_file_data = b''.join(f.readlines())
                image_data[file] = image_file_data

    for file_name, image in image_data.items():
        container.add_file(file_name, image)

    # Get the compressed data
    compressed_data = container.get_compressed_container()

    print("Compression done")

    with open("./htfs_files.bin", "wb") as f:
        f.write(compressed_data)

    print("Wrote bin")

    # To extract a specific file from the compressed data
    try:
        decompressed_images = []
        for i in range(len(image_data)):
            decompressed_image = container.extract_file(compressed_data, i)
            decompressed_images.append(decompressed_image)
    except Exception as e:
        print("Indexing not possible, error", e, "\n")
        decompressed_images = []
        for file_name in image_data.keys():
            decompressed_image = container.extract_file(compressed_data, file_name)
            decompressed_images.append(decompressed_image)
    compression_ratio = len(compressed_data) / sum(len(x) for x in image_data.values())

    print(f"Original size: {sum(len(x) for x in image_data.values())} bytes")
    print(f"Compressed size: {len(compressed_data)} bytes")
    print(f"Compression ratio: {compression_ratio:.2f}")

    for i, decompressed_image in enumerate(decompressed_images):
        with open(f"./decompressed_images/image{i}.HTSF", "wb") as f:
            f.write(decompressed_image)

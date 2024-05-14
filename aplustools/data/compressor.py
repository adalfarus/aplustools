import lzma
import brotli
import json
import os
import zstandard as zstd
import py7zr
import io
from typing import Union, Tuple, List, Optional
from aplustools.utils.genpass import CryptUtils
from aplustools.data import encode_int, decode_int


class EmptyChunkProcessor:
    def process(self, data_chunk: bytes) -> bytes:
        return data_chunk

    def unprocess(self, processed_chunk: bytes) -> bytes:
        return processed_chunk


class BrotliChunkCompressor(EmptyChunkProcessor):
    def __init__(self, quality: int = 11):  # Maximum compression quality
        self.quality = quality

    def process(self, data_chunk: bytes) -> bytes:
        # Compress the data chunk with Brotli
        return brotli.compress(data_chunk, quality=self.quality)

    def unprocess(self, processed_chunk: bytes) -> bytes:
        # Decompress the data chunk with Brotli
        return brotli.decompress(processed_chunk)

    @staticmethod
    def add_markers(data, start_marker, end_marker):
        # Add start and end markers to the data
        return start_marker + data + end_marker


class LZMAChunkCompressor(EmptyChunkProcessor):
    def __init__(self, preset=lzma.PRESET_EXTREME):
        self.preset = preset

    def process(self, data_chunk: bytes) -> bytes:
        # Compress the data chunk with LZMA
        return lzma.compress(data_chunk, preset=self.preset)

    def unprocess(self, processed_chunk: bytes) -> bytes:
        # Decompress the data chunk with LZMA
        return lzma.decompress(processed_chunk)


class ZstdChunkCompressor(EmptyChunkProcessor):
    def __init__(self, level: int=3):
        self.compressor = zstd.ZstdCompressor(level=level)
        self.decompressor = zstd.ZstdDecompressor()

    def process(self, data_chunk: bytes) -> bytes:
        return self.compressor.compress(data_chunk)

    def unprocess(self, processed_chunk: bytes) -> bytes:
        return self.decompressor.decompress(processed_chunk)


class LZMA2ChunkCompressor(EmptyChunkProcessor):
    def process(self, data_chunk: bytes) -> bytes:
        with io.BytesIO() as buffer, py7zr.SevenZipFile(buffer, 'w', filters=[{'id': py7zr.FILTER_LZMA2}]) as archive:
            # Create a file-like object from data_chunk
            file_like_data = io.BytesIO(data_chunk)
            archive.write({"data": file_like_data})
            buffer.seek(0)  # Reset buffer position to the beginning
            return buffer.getvalue()

    def unprocess(self, processed_chunk: bytes) -> bytes:
        with io.BytesIO(processed_chunk) as input_buffer, py7zr.SevenZipFile(input_buffer, 'r') as archive:
            output_buffer = io.BytesIO()
            archive.extractall(path=output_buffer)
            output_buffer.seek(0)  # Reset buffer position to the beginning
            return output_buffer.read()


class AESChunkEncryptor(EmptyChunkProcessor):
    def __init__(self, key: Optional[bytes] = None):
        self.key = key if key is not None else CryptUtils.generate_aes_key(128)

    @staticmethod
    def pack_aes_data(iv: bytes, encrypted_data: bytes, tag: bytes) -> bytes:
        iv_len_encoded = len(iv).to_bytes(1, "big")  # Maximum length of 128
        tag_len_encoded = len(tag).to_bytes(1, "big")  # Maximum length of 128
        return iv_len_encoded + iv + tag_len_encoded + tag + encrypted_data

    @staticmethod
    def unpack_aes_data(data: bytes):
        iv_len = decode_int(data[:1])

        iv_start = 1
        iv_end = iv_start + iv_len
        iv = data[iv_start:iv_end]

        tag_len = decode_int(data[iv_end:iv_end+1])
        tag_start = iv_end+1
        tag_end = tag_start + tag_len
        tag = data[tag_start:tag_end]

        encrypted_data = data[tag_end:]
        return iv, encrypted_data, tag

    def process(self, data_chunk: bytes) -> bytes:
        iv, encrypted_data, tag = CryptUtils.aes_encrypt(data_chunk, key=self.key)
        return self.pack_aes_data(iv, encrypted_data, tag)

    def unprocess(self, processed_chunk: bytes) -> bytes:
        iv, encrypted_data, tag = self.unpack_aes_data(processed_chunk)
        return CryptUtils.aes_decrypt(iv, encrypted_data, tag, key=self.key)


class DESChunkEncryptor(AESChunkEncryptor):
    def __int__(self, key: Optional[bytes] = None):
        self.key = key if key is not None else CryptUtils.generate_des_key(64)

    def process(self, data_chunk: bytes) -> bytes:
        iv, encrypted_data, tag = CryptUtils.des_encrypt(data_chunk, key=self.key)
        return self.pack_aes_data(iv, encrypted_data, tag)

    def unprocess(self, processed_chunk: bytes) -> bytes:
        iv, encrypted_data, tag = self.unpack_aes_data(processed_chunk)
        return CryptUtils.des_decrypt(iv, encrypted_data, tag, key=self.key)


class RSAChunkEncryptor(EmptyChunkProcessor):
    def __init__(self, private_key_bytes: bytes = None):
        self.key = CryptUtils.load_private_key(private_key_bytes if private_key_bytes is not None else CryptUtils.generate_rsa_key(1024)[0])
        self._public_key = self.key.public_key()

    def process(self, data_chunk: bytes) -> bytes:
        return CryptUtils.rsa_encrypt(data_chunk, public_key=self._public_key)

    def unprocess(self, processed_chunk: bytes) -> bytes:
        return CryptUtils.rsa_decrypt(processed_chunk, private_key=self.key)


class FileContainerV4:
    def __init__(self, compressor: EmptyChunkProcessor, encryptor: EmptyChunkProcessor, file_path: str, container_start: int, container_end: int,
                 block_size: int = 1024 * 1024, load_now: bool = True):
        self.compressor = compressor
        self.block_size = block_size
        self.current_block = bytearray()

        self.file_path = file_path
        self.container_start = container_start
        self.container_end = container_end
        self.file_info = {}
        self.index_to_name = []
        self.block_offsets = []

        if load_now:
            if os.path.exists(file_path):
                self.load_compressed_container_metadata()
            else:
                with open(file_path, "wb") as f:
                    f.seek(container_start)
                    f.write(b'\0' * (self.container_end - self.container_start))

    def load_compressed_container_metadata(self):
        """Loads only the metadata for the compressed container part within the specified range."""
        with open(self.file_path, 'rb') as file:
            file.seek(self.container_start)
            index_length_bytes = file.read(4)
            index_length = int.from_bytes(index_length_bytes, 'big')

            if index_length > self.container_end - self.container_start - 4:
                raise ValueError("Index size is larger than the designated container range.")

            compressed_index_data = file.read(index_length)
            index_data = self.compressor.unprocess(compressed_index_data)
            index = json.loads(index_data)
            self.file_info = index['file_info']
            self.index_to_name = index['index_to_name']
            self.block_offsets = index['block_offsets']

    def _compress_current_block(self):
        if self.current_block:
            compressed_block = self.compressor.process(self.current_block)
            self.block_offsets.append({'start': len(self.compressed_data), 'length': len(compressed_block)})
            self.compressed_data.extend(compressed_block)
            self.current_block = bytearray()

    def add_file(self, filename: str, data: bytes) -> int:
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

        return file_index

    def get_entire_compressed_container(self) -> bytes:
        self._compress_current_block()  # Compress any remaining data in the current block
        index_data = json.dumps({'file_info': self.file_info, 'block_offsets': self.block_offsets, 'index_to_name': self.index_to_name}).encode()
        compressed_index_data = self.compressor.process(index_data)
        index_length = len(compressed_index_data).to_bytes(4, 'big')
        return index_length + compressed_index_data + self.compressed_data

    def extract_file_partial(self, file_identifier: Union[str, int], offset: int, length: int) -> bytes:
        """Extracts a part of a file by direct access, only within the compressed container range."""
        filename = file_identifier if isinstance(file_identifier, str) else self.index_to_name[file_identifier]
        file_info = self.file_info[filename]
        block_info = self.block_offsets[file_info['block_index']]

        with open(self.file_path, 'rb') as file:
            # Calculate the position and ensure it's within the designated container range
            start_position = self.container_start + block_info['start']
            if start_position < self.container_start or start_position > self.container_end:
                raise ValueError("Block start position is outside of the designated container range.")

            file.seek(start_position)
            compressed_block = file.read(block_info['length'])
            decompressed_block = self.compressor.unprocess(compressed_block)

        # Calculate the actual positions in the decompressed block
        actual_start = file_info['start'] + offset
        actual_end = actual_start + length

        return decompressed_block[actual_start:actual_end]

    def remove_file(self, file_identifier: Union[str, int]):
        """Removes a file's metadata and index but does not modify the actual compressed data."""
        filename = file_identifier if isinstance(file_identifier, str) else self.index_to_name[file_identifier]

        # Remove file info and update mappings
        del self.file_info[filename]
        self.index_to_name = [name for name in self.index_to_name if name != filename]
        self.block_offsets = [offset for offset in self.block_offsets if self.file_info.get(filename, {}).get('block_index') != offset]

    def get_compressed_container_info(self) -> Tuple[int, List[str]]:
        """Loads and returns basic info about the compressed container."""
        if not self.file_info:
            self.load_compressed_container_metadata()
        return len(self.file_info), self.index_to_name

    def update_compressed_container(self):
        """Updates the metadata index in the compressed file to reflect changes."""
        index_data = json.dumps({'file_info': self.file_info, 'block_offsets': self.block_offsets, 'index_to_name': self.index_to_name}).encode()
        compressed_index_data = self.compressor.process(index_data)
        index_length = len(compressed_index_data).to_bytes(4, 'big')

        with open(self.file_path, 'r+b') as file:
            file.seek(self.container_start)
            file.write(index_length + compressed_index_data)  # Overwrite old index

    def defragment(self):
        "metadatawrtie" "mdw"
        "metadataread" "mdr"
        "metdadataclear" "mdc"

        op_code = "mdw"
        start_pos = 241 + self.container_start
        end_pos = 256 + self.container_start
        print(f"{op_code} | {start_pos}-{end_pos}")
        """Optimizes the current blocks into one continuous block."""
        with open(self.file_path, 'r+b') as file:
            # Seek to the start of the container
            file.seek(self.container_start)
            next_write_position = 0
            updated_block_offsets = []

            # Read each block, decompress, recompress (if needed), and write back contiguously
            for block_info in self.block_offsets:
                file.seek(self.container_start + block_info['start'])
                compressed_block = file.read(block_info['length'])
                updated_block_offsets.append({
                    'start': next_write_position,
                    'length': block_info['length']
                })
                # Write block back at the new position
                file.seek(self.container_start + next_write_position)
                file.write(compressed_block)
                next_write_position += block_info['length']

            # Fill the rest of the container with zeros to clear leftover data
            remaining_space = self.container_end - (self.container_start + next_write_position)
            if remaining_space < 0:
                raise ValueError("Defragmentation would overflow the container bounds.")

            file.write(b'\0' * remaining_space)

            # Update block offsets with their new positions
            self.block_offsets = updated_block_offsets

            # Optionally update the container's metadata here as well

    def clear_unneeded(self):
        pass

    def optimize(self):
        """Shifts all"""
        self.defragment()
        self.delete_unneeded()

    def delete_unneeded(self):
        pass


def local_test():
    try:
        compressor = BrotliChunkCompressor()
        container = FileContainerV3(compressor, block_size=2048 * 2048)

        data = {}
        for root, dirs, files in os.walk("./test_data"):
            for file in files:
                with open(os.path.join(root, file), "rb") as f:
                    image_file_data = b''.join(f.readlines())
                    data[file] = image_file_data

        # for file_name, image in data.items():
        #     container.add_file(file_name, image)
        #
        # # Get the compressed data
        # compressed_data = container.get_compressed_container()
        #
        # print("Compression done")
        #
        # with open("./test_data/files.bin", "wb") as f:
        #     f.write(compressed_data)
        #
        # print("Wrote bin")

        with open("./test_data/files.bin", "rb") as f:
            compressed_data = f.read()

        print("Read bin")

        # To extract a specific file from the compressed data
        try:
            decompressed_files = []
            for i in range(len(data)):
                decompressed_file = container.extract_file(compressed_data, i)
                decompressed_files.append(decompressed_file)
        except Exception as e:
            print("Indexing not possible, error", e, "\n")
            decompressed_files = []
            for file_name in data.keys():
                decompressed_file = container.extract_file(compressed_data, file_name)
                decompressed_files.append(decompressed_file)
        compression_ratio = len(compressed_data) / sum(len(x) for x in data.values())

        print(f"Original size: {sum(len(x) for x in data.values())} bytes")
        print(f"Compressed size: {len(compressed_data)} bytes")
        print(f"Compression ratio: {compression_ratio:.2f}")

        for i, decompressed_file in enumerate(decompressed_files):
            with open(f"./test_data/file_{i}.ext", "wb") as f:
                f.write(decompressed_file)
    except Exception as e:
        print(f"An error occurred: {e}")
        return False
    print("Test completed successfully.")
    return True


if __name__ == "__main__":
    local_test()

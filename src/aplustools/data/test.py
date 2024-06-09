import os
import json
from typing import Union, Tuple, List, Literal, Optional, Any
from src.aplustools import CryptUtils
import brotli


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


class AESChunkEncryptor(EmptyChunkProcessor):
    def __init__(self, key: Optional[bytes] = None):
        self.key = key if key is not None else CryptUtils.generate_aes_key(128)

    def process(self, data_chunk: bytes) -> bytes:
        iv, encrypted_data, tag = CryptUtils.aes_encrypt(data_chunk, key=self.key)
        return CryptUtils.pack_ae_data(iv, encrypted_data, tag)

    def unprocess(self, processed_chunk: bytes) -> bytes:
        iv, encrypted_data, tag = CryptUtils.unpack_ae_data(processed_chunk)
        return CryptUtils.aes_decrypt(iv, encrypted_data, tag, key=self.key)


class FileContainerV4:
    tag_to_processor = {
        "empty": EmptyChunkProcessor,
        "aes": AESChunkEncryptor,
        "brotli": BrotliChunkCompressor
    }

    def __init__(self, compressor: EmptyChunkProcessor, encryptor: EmptyChunkProcessor, file_path: str,
                 container_start: int = 0, container_end: Union[int, Literal["end"]] = "end",
                 block_size: int = 1024 * 1024, create_now: bool = True):
        self._compressor = compressor
        self._encryptor = encryptor
        self._block_size = block_size
        self._current_block = bytearray()

        self.file_path = file_path
        self._container_start = container_start
        self.container_end = container_end
        self._file_info = {}
        self._index_to_name = []
        self._block_offsets = []

        if create_now and not os.path.exists(file_path):
            with open(file_path, "wb") as f:
                f.seek(container_start)
                f.write(b'\0' * (self.container_end - self._container_start))
        else:
            with open(file_path, "rb") as f:
                *_, self._file_info, self._index_to_name, self._block_offsets, self._metadata_length = self._read_metadata_from_position(self._container_start, f)

    @classmethod
    def from_file(cls, file_path: str, key: Optional[Any] = None) -> "FileContainerV4":
        return cls.from_file_part(0, file_path, key)

    @classmethod
    def _read_metadata_from_position(cls, start_position, file, key: Optional[Any] = None):
        file.seek(start_position)
        processor_tags_length_bytes = file.read(1)
        processor_tags_length = int.from_bytes(processor_tags_length_bytes, "big")
        processor_tags = file.read(processor_tags_length)
        processor_data = json.loads(processor_tags)

        try:
            compressor: EmptyChunkProcessor = cls.tag_to_processor[processor_data.get("compr", "brotli")]()
            encryptor: EmptyChunkProcessor = cls.tag_to_processor[processor_data.get("encry", "aes")](key=key)
        except KeyError:
            raise ValueError(f"The used compressor or encryptor is not in tag_to_processor.")

        index_length_bytes_bytes = file.read(4)
        index_length_bytes = file.read(int.from_bytes(index_length_bytes_bytes, "big"))
        index_length = int.from_bytes(index_length_bytes, 'big')

        encrypted_index_data = file.read(index_length)
        compressed_index_data = encryptor.unprocess(encrypted_index_data)
        index_data = compressor.unprocess(compressed_index_data)
        index = json.loads(index_data)

        container_len = index['container_len']
        container_end = index['container_end']
        block_size = index['block_size']

        if container_len > container_end - start_position:
            raise ValueError("Container size is larger than the designated container range.")

        file_info = index['file_info']
        index_to_name = index['index_to_name']
        block_offsets = index['block_offsets']

        return (compressor, encryptor, container_len, container_end, block_size, file_info, index_to_name,
                block_offsets, index_length)

    @classmethod
    def from_file_part(cls, start_position: int, file_path: str, key: Optional[Any] = None) -> "FileContainerV4":
        with open(file_path, "rb") as f:
            compr, encry, container_len, container_end, block_size, *_ = cls._read_metadata_from_position(
                start_position, f, key)

        return FileContainerV4(compr, encry, file_path, start_position, container_end, block_size)

    @staticmethod
    def _null_bytes(start_position, length, f):
        f.seek(start_position)
        f.write(b'\0' * length)

    def change_container_start(self, new_start_position: int):
        with open(self.file_path, "r+b") as f:
            self._null_bytes(new_start_position, self._metadata_length, f)
            self._move_block((self._container_start, self._container_start + self._metadata_length),
                             (new_start_position, new_start_position + self._metadata_length), f)

    @staticmethod
    def _move_block(from_chunk: tuple, to_chunk: tuple, f):
        from_start_position, from_end_position = from_chunk
        to_start_position, to_end_position = to_chunk

        f.seek(from_start_position)
        to_write = f.read(from_end_position - from_start_position)

        f.seek(to_start_position)
        bytes_to_overwrite = f.read(to_end_position - to_start_position)

        if bytes_to_overwrite != b"\0" * len(bytes_to_overwrite):
            raise ValueError("All bytes in the to_chunk have to be null.")

        f.seek(to_start_position)

        f.write(to_write)


    def load_compressed_container_metadata(self):
        """Loads only the metadata for the compressed container part within the specified range."""
        with open(self.file_path, 'rb') as file:
            file.seek(self._container_start)
            index_length_bytes = file.read(4)
            index_length = int.from_bytes(index_length_bytes, 'big')

            if index_length > self.container_end - self._container_start - 4:
                raise ValueError("Index size is larger than the designated container range.")

            compressed_index_data = file.read(index_length)
            index_data = self._compressor.decompress(compressed_index_data)
            index = json.loads(index_data)
            self._file_info = index['file_info']
            self._index_to_name = index['index_to_name']
            self._block_offsets = index['block_offsets']  # Have the end of the container saved
            # Have the length of the container saved (Check against end)
            # Automatically refactor block placement when possible.

    def _compress_current_block(self):
        if self._current_block:
            compressed_block = self._compressor.compress(self._current_block)
            self._block_offsets.append({'start': len(self.compressed_data), 'length': len(compressed_block)})
            self.compressed_data.extend(compressed_block)
            self._current_block = bytearray()

    def add_file(self, filename: str, data: bytes) -> int:
        if len(self._current_block) + len(data) > self._block_size:
            self._compress_current_block()

        file_index = len(self._index_to_name)
        self._index_to_name.append(filename)
        self._file_info[filename] = {
            'index': file_index,
            'block_index': len(self._block_offsets),
            'start': len(self._current_block),
            'length': len(data)
        }
        self._current_block.extend(data)

        if len(self._current_block) >= self._block_size:
            self._compress_current_block()

        return file_index

    def get_entire_compressed_container(self) -> bytes:
        self._compress_current_block()  # Compress any remaining data in the current block
        index_data = json.dumps({'file_info': self._file_info, 'block_offsets': self._block_offsets, 'index_to_name': self._index_to_name}).encode()
        compressed_index_data = self._compressor.compress(index_data)
        index_length = len(compressed_index_data).to_bytes(4, 'big')
        return index_length + compressed_index_data + self.compressed_data

    def extract_file_partial(self, file_identifier: Union[str, int], offset: int, length: int) -> bytes:
        """Extracts a part of a file by direct access, only within the compressed container range."""
        filename = file_identifier if isinstance(file_identifier, str) else self._index_to_name[file_identifier]
        file_info = self._file_info[filename]
        block_info = self._block_offsets[file_info['block_index']]

        with open(self.file_path, 'rb') as file:
            # Calculate the position and ensure it's within the designated container range
            start_position = self._container_start + block_info['start']
            if start_position < self._container_start or start_position > self.container_end:
                raise ValueError("Block start position is outside of the designated container range.")

            file.seek(start_position)
            compressed_block = file.read(block_info['length'])
            decompressed_block = self._compressor.decompress(compressed_block)

        # Calculate the actual positions in the decompressed block
        actual_start = file_info['start'] + offset
        actual_end = actual_start + length

        return decompressed_block[actual_start:actual_end]

    def remove_file(self, file_identifier: Union[str, int]):
        """Removes a file's metadata and index but does not modify the actual compressed data."""
        filename = file_identifier if isinstance(file_identifier, str) else self._index_to_name[file_identifier]

        # Remove file info and update mappings
        del self._file_info[filename]
        self._index_to_name = [name for name in self._index_to_name if name != filename]
        self._block_offsets = [offset for offset in self._block_offsets if self._file_info.get(filename, {}).get('block_index') != offset]

    def get_compressed_container_info(self) -> Tuple[int, List[str]]:
        """Loads and returns basic info about the compressed container."""
        if not self._file_info:
            self.load_compressed_container_metadata()
        return len(self._file_info), self._index_to_name

    def update_compressed_container(self):
        """Updates the metadata index in the compressed file to reflect changes."""
        index_data = json.dumps({'file_info': self._file_info, 'block_offsets': self._block_offsets, 'index_to_name': self._index_to_name}).encode()
        compressed_index_data = self._compressor.compress(index_data)
        index_length = len(compressed_index_data).to_bytes(4, 'big')

        with open(self.file_path, 'r+b') as file:
            file.seek(self._container_start)
            file.write(index_length + compressed_index_data)  # Overwrite old index

    def defragment(self):
        "metadatawrtie" "mdw"
        "metadataread" "mdr"
        "metdadataclear" "mdc"

        op_code = "mdw"
        start_pos = 241 + self._container_start
        end_pos = 256 + self._container_start
        print(f"{op_code} | {start_pos}-{end_pos}")
        """Optimizes the current blocks into one continuous block."""
        with open(self.file_path, 'r+b') as file:
            # Seek to the start of the container
            file.seek(self._container_start)
            next_write_position = 0
            updated_block_offsets = []

            # Read each block, decompress, recompress (if needed), and write back contiguously
            for block_info in self._block_offsets:
                file.seek(self._container_start + block_info['start'])
                compressed_block = file.read(block_info['length'])
                updated_block_offsets.append({
                    'start': next_write_position,
                    'length': block_info['length']
                })
                # Write block back at the new position
                file.seek(self._container_start + next_write_position)
                file.write(compressed_block)
                next_write_position += block_info['length']

            # Fill the rest of the container with zeros to clear leftover data
            remaining_space = self.container_end - (self._container_start + next_write_position)
            if remaining_space < 0:
                raise ValueError("Defragmentation would overflow the container bounds.")

            file.write(b'\0' * remaining_space)

            # Update block offsets with their new positions
            self._block_offsets = updated_block_offsets

            # Optionally update the container's metadata here as well

    def clear_unneeded(self):
        pass

    def optimize(self):
        """Shifts all"""
        self.defragment()
        self.delete_unneeded()

    def delete_unneeded(self):
        pass



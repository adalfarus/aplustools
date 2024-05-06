import os
import json
from typing import Union, Tuple, List, Literal


class EmptyChunkCompressor:
    def compress(self, data_chunk: bytes) -> bytes:
        return data_chunk

    def decompress(self, compressed_chunk: bytes) -> bytes:
        return compressed_chunk


class FileContainerV4:
    def __init__(self, compressor: EmptyChunkCompressor, file_path: str, container_start: int,
                 container_end: Union[int, Literal["end"]], block_size: int = 1024 * 1024, load_now: bool = True):
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
            index_data = self.compressor.decompress(compressed_index_data)
            index = json.loads(index_data)
            self.file_info = index['file_info']
            self.index_to_name = index['index_to_name']
            self.block_offsets = index['block_offsets']

    def _compress_current_block(self):
        if self.current_block:
            compressed_block = self.compressor.compress(self.current_block)
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
        compressed_index_data = self.compressor.compress(index_data)
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
            decompressed_block = self.compressor.decompress(compressed_block)

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
        compressed_index_data = self.compressor.compress(index_data)
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



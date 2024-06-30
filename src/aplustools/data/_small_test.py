from ..package.timid import TimidTimer
from ..data import nice_number as nn
from typing import Optional


class NotEnoughSpaceException(Exception):
    def __init__(self, curr_pointer, available_space, needed_space):
        super().__init__(f"Current Pointer: {nn(curr_pointer)}; Space: {nn(available_space)}/{nn(needed_space)}")


class Test:
    def __init__(self):
        self._block_offsets = [
            {'start': 17_992, 'length': 1024},
            {'start': 19_992, 'length': 1024},
            {'start': 200_992, 'length': 1024},  # Block 3
            {'start': 1_992, 'length': 1024},
            {'start': 199_992, 'length': 1024},
        ]
        self._file_to_block = [{"block": 3, "start": 0, "length": 1024, "next": None}]
        self._container_start = 1_800
        self._container_end = 1_201_000
        self._chunks_buffer = []
        self.file_info = {}

    def _get_chunks(self):
        if not self._chunks_buffer:
            chunks = [(i, offset['start'], offset['length']) for i, offset in enumerate(self._block_offsets)]
            chunks.sort(key=lambda x: x[1])
            self._chunks_buffer = chunks
        return self._chunks_buffer

    def _invalidate_buffer(self):
        self._chunks_buffer = []

    def _get_closest_chunk(self, size):
        chunks = self._get_chunks()
        curr_pointer = self._container_start

        for _, start, length in chunks:
            space = start - curr_pointer
            if space >= size:
                break
            curr_pointer = start + length

        if self._container_end - curr_pointer >= size:
            return curr_pointer
        return None

    def _make_space(self, needed_space: Optional[int] = None) -> int:
        chunks = self._get_chunks()
        curr_pointer = self._container_start
        self._invalidate_buffer()

        for blck_index, offset, length in chunks:
            if offset - curr_pointer >= needed_space:
                return curr_pointer
            elif curr_pointer != offset:
                self._move_block((offset, offset + length), (curr_pointer, curr_pointer + length))
                self._block_offsets[blck_index] = {'start': curr_pointer, 'length': length}
                curr_pointer += length

        if self._container_end - curr_pointer >= needed_space:
            return curr_pointer

        raise NotEnoughSpaceException(curr_pointer, self._container_end - curr_pointer, needed_space)

    @staticmethod
    def _null_bytes(start_position, length):
        return  # Doesn't need to do anything

    @classmethod
    def _move_block(cls, from_chunk: tuple, to_chunk: tuple):
        from_start_position, from_end_position = from_chunk
        to_start_position, to_end_position = to_chunk

        # Moving the blocks
        # ...

        cls._null_bytes(from_start_position, from_end_position - from_start_position)

    def _pack_block_info(self, block):
        from ..data import bytes_length, set_bits, nice_bits, encode_positive_int

        result = set_bits(int(0).to_bytes(), 0, nice_bits(encode_positive_int(bytes_length(len(block["block"])))))
        # block_len =
        # result |= block_len
        # todo: Finish


    def add(self, name, contents):
        size = len(contents)
        required_space = int(size * 1.10)  # Allow up to 10 percent bigger "compression" and encryption

        position = self._get_closest_chunk(required_space)
        if position is None:
            try:
                position = self._make_space(required_space)  # De-fragment until a space of size len(contents) is freed.
            except NotEnoughSpaceException as e:
                print(f"Container ran out of space: {e}")
                return False

        block_size = 1024
        remaining_size = size

        # Initialize file info
        self.file_info[name] = {'start_block': len(self._block_offsets), 'length': size, 'blocks': []}

        while remaining_size > 0:
            chunk_size = min(block_size, remaining_size)
            self._block_offsets.append({"start": position, "length": chunk_size})
            self.file_info[name]['blocks'].append(self._pack_block_info({'block': len(self._block_offsets) - 1,
                                                                         'start': 0, 'length': chunk_size}))
            remaining_size -= chunk_size
            position += chunk_size
        return True


if __name__ == "__main__":
    test = Test()
    timer = TimidTimer()
    result = test.add("My Naame", "C" * 1_000_000) and test.add("My Naamee", "C" * 176_113)
    timer.stop()
    print(test.file_info)
    print(test._block_offsets)
    print("!" if result else "?", timer.get())

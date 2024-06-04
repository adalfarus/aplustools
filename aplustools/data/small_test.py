from aplustools.package.timid import TimidTimer
from typing import Optional


class NotEnoughSpaceException(Exception):
    def __init__(self, curr_pointer, needed_space):
        super().__init__(f"CP: {curr_pointer}; ND {needed_space}")


class Test:
    def __init__(self):
        self._block_offsets = [
            {
                'start': 17_992,
                'length': 1024  # 1 mb
            },
            {
                'start': 19_992,
                'length': 1024  # 1 mb
            },
            {
                'start': 200_992,
                'length': 1024  # 1 mb
            },
            {
                'start': 1_992,
                'length': 1024  # 1 mb
            },
            {
                'start': 199_992,
                'length': 1024  # 1 mb
            },
        ]
        self._container_start = 1_800
        self._container_end = 201_000
        self._chunks_buffer = []

    def _get_chunks(self):
        if not self._chunks_buffer:
            chunks = []
            for offset in self._block_offsets:
                (_, start), (__, length) = offset.items()
                chunks.append((start, length))

            chunks.sort(key=lambda x: x[0])
            self._chunks_buffer = chunks
        return self._chunks_buffer

    def _invalidate_buffer(self):
        self._chunks_buffer = []

    def _get_closest_chunk(self, size):
        chunks = self._get_chunks()

        curr_pointer = self._container_start
        for sort_chunk in chunks:
            space = sort_chunk[0] - curr_pointer
            if space >= size:
                break
            curr_pointer = sum(sort_chunk)

        if curr_pointer < self._container_end:
            return curr_pointer
        return None

    def defragment(self, needed_space: Optional[int] = None) -> int:
        chunks = self._get_chunks()
        curr_pointer = self._container_start

        self._invalidate_buffer()  # We will most certainly change it so instead of many ifs in the loop,
        i = 0                      # invalidate it once here
        while i < len(chunks):  # We will change the list as we iterate
            chunk = chunks[i]
            chunk_range = (chunk[0], chunk[0] + chunk[1])

            if curr_pointer != chunk[0]:
                self._move_block(chunk_range, (curr_pointer, curr_pointer + chunk[1]))


            i += 1

        raise NotEnoughSpaceException(self._container_start, needed_space)

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

    def add(self, name, contents):
        position = self._get_closest_chunk(len(contents))
        if position is None:
            try:
                position = self.defragment(len(contents))  # De-fragment until a space of size len(contents) is freed.
            except NotEnoughSpaceException as e:
                print(f"Container ran out of space: {e}")
                return False
        return True


if __name__ == "__main__":
    test = Test()
    timer = TimidTimer()
    result = test.add("My Naame", "C" * 1_000_000)
    timer.stop()
    print("!" if result else "?", timer.get())

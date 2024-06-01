import re

class Protocol:
    def __init__(self, exec_code_start, comm_code, exec_code_end):
        self._exec_code_start = exec_code_start
        self._comm_code = comm_code
        self._exec_code_end = exec_code_end

    def get_exec_code_delimiters(self) -> tuple:
        return re.escape(self._exec_code_start) + re.escape(self._comm_code), re.escape(self._exec_code_end)

class BufferProcessor:
    def __init__(self, protocol, buffer):
        self._protocol = protocol
        self._buffer = buffer

    def process_buffer(self):
        # Process complete and partial messages in buffer
        exec_start, exec_end = self._protocol.get_exec_code_delimiters()
        pattern = fr'({exec_start}.*?{exec_end})'

        # Find all matches and their positions
        matches = list(re.finditer(pattern, self._buffer))

        split_parts = []
        last_end = 0

        for match in matches:
            start, end = match.span()

            # Add the text before the match
            if start > last_end:
                split_parts.append(self._buffer[last_end:start])

            # Add the matched sequence
            split_parts.append(self._buffer[start:end])

            last_end = end

        # Add any remaining text after the last match
        if last_end < len(self._buffer):
            split_parts.append(self._buffer[last_end:])

        return split_parts

# Example usage
exec_code_start = '['
comm_code = 'y2GTmhYrMx8XotC2aVFkpfTrFGaWYlxZADTC_lcO0jPz2HP0cQ'
exec_code_end = ']'
buffer = "\x1b[0m\x1b[0;32;40m[y2GTmhYrMx8XotC2aVFkpfTrFGaWYlxZADTC_lcO0jPz2HP0cQ::NEWLINE] Grass [y2GTmhYrMx8XotC2aVFkpfTrFGaWYlxZADTC_lcO0jPz2HP0cQ::IN::Please input the [SECURE] password: ]DDxxcas"

protocol = Protocol(exec_code_start, comm_code, exec_code_end)
processor = BufferProcessor(protocol, buffer)

split_parts = processor.process_buffer()

print(split_parts)

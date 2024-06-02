from aplustools.io.environment import strict
from typing import Tuple, Optional, Any
import base64
import json
import os


class DummyProtocol:
    @staticmethod
    def get_exec_code_delimiters(self) -> tuple:
        return "", ""

    @staticmethod
    def get_control_code(self, control_code: str, add_in: Optional[str] = None) -> str:
        return control_code + add_in

    @staticmethod
    def validate_control_code(self, exec_code: str) -> str:
        return exec_code
    
    
@strict
class ControlCodeProtocol:
    def __init__(self, comm_code: Optional[str] = None, exec_code_delimiter: str = "::", exec_code_start: str = "[",
                 exec_code_end: str = "]", control_codes: Optional[dict] = None):
        self._comm_code = comm_code
        if not self._comm_code:
            self._comm_code = self._generate_random_string(50)
        self._exec_code_delimiter = exec_code_delimiter
        self._exec_code_start = exec_code_start
        self._exec_code_end = exec_code_end
        self._control_codes = control_codes if control_codes is not None else {
            "end": "NEWLINE", "shutdown": "SHUTDOWN 0xC000013A", "input": "IN"
        }

    def get_exec_code_delimiters(self) -> tuple:
        return self._exec_code_start, self._exec_code_end

    @staticmethod
    def _generate_random_string(length):
        # Calculate how many bytes are needed to get the desired string length after Base64 encoding
        bytes_length = (length * 3) // 4
        random_bytes = os.urandom(bytes_length)

        # Encode these bytes into a Base64 string
        random_string_base64 = base64.urlsafe_b64encode(random_bytes).decode('utf-8')

        # Return the required length
        return random_string_base64[:length]

    def get_control_code(self, control_code: str, add_in: Optional[str] = None) -> str:
        add_in_str = f"{self._exec_code_delimiter}{add_in}" if add_in else ""
        return (f"{self._exec_code_start}"
                f"{self._comm_code}{self._exec_code_delimiter}{self._control_codes.get(control_code.lower())}"
                f"{add_in_str}{self._exec_code_end}")

    def validate_control_code(self, exec_code: str) -> Tuple[str, Optional[str]]:
        if exec_code.startswith(self._exec_code_start) and exec_code.endswith(self._exec_code_end):
            # Remove the start and end markers
            plain_code = exec_code[len(self._exec_code_start):-len(self._exec_code_end)]

            shipped_code = plain_code[:len(self._comm_code)]
            if shipped_code == self._comm_code:
                rest = plain_code[len(self._comm_code) + len(self._exec_code_delimiter):].split(
                    self._exec_code_delimiter, 1) + [None]
                control_code, add_in = rest[:2]
                for key, value in self._control_codes.items():
                    if control_code == value:
                        return key, add_in
                return "Invalid control code", None
            return "Invalid key", None
        else:
            # Raise an error if the string does not have the required start and end markers
            raise ValueError("String does not start and end with required markers")

    def serialize(self):
        return json.dumps({
            "comm_code": self._comm_code,
            "exec_delimiter": self._exec_code_delimiter,
            "exc_code_start": self._exec_code_start,
            "exc_code_end": self._exec_code_end,
            "status_codes": self._control_codes
        })

    @staticmethod
    def deserialize(serialized_data):
        data = json.loads(serialized_data)
        return ControlCodeProtocol(data["comm_code"], data["exec_delimiter"], data["exc_code_start"], data["exc_code_end"], data["status_codes"])
    

class _ControlCode:
    def __init__(self, control_code: str, add_in: str):
        self.code = control_code
        self.add = add_in

    def __repr__(self):
        return f"ControlCode(code={self.code}, add={self.add})"


def is_control_code(obj: Any) -> bool:
    return isinstance(obj, _ControlCode)

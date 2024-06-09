from src.aplustools import CryptUtils
from typing import Dict, Any, Union
import sqlite3
import os
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import base64


class SecureDatabase:
    def __init__(self, db_connection):
        self.conn = db_connection

    def _get_all_tables(self) -> tuple:
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = cursor.fetchall()
        return tuple(table[0] for table in tables)

    def _get_all_columns(self, table_name) -> tuple:
        cursor = self.conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns_info = cursor.fetchall()
        column_names = [info[1] for info in columns_info]
        return tuple(column_names)

    def _add_encrypted_column(self, table_name):
        cursor = self.conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns_info = cursor.fetchall()
        column_names = [info[1] for info in columns_info]

        if "encrypted" not in column_names:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN encrypted TEXT;")
            self.conn.commit()

    def _encrypt_data(self, data: str, password: str, return_in_base64: bool = False) -> Union[bytes, str]:
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = kdf.derive(password.encode())

        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        encrypted_data = encryptor.update(data.encode()) + encryptor.finalize()

        if return_in_base64:
            # Return base64 encoded string
            return base64.b64encode(salt + iv + encryptor.tag + encrypted_data).decode('utf-8')
        return salt + iv + encryptor.tag + encrypted_data

    def encrypt(self, encryption_config: Dict[str, Any], password: str, save_in_base64: bool = False):
        cursor = self.conn.cursor()

        got = encryption_config.get("ALL", None)
        if got is not None:
            encryption_config = {table: {"columns": got, "rows": "ALL"} for table in self._get_all_tables()}

        for table, config in encryption_config.items():
            columns = config.get("columns", "ALL")
            rows = config.get("rows", "ALL")

            self._add_encrypted_column(table)

            # if columns == "ALL":
            #     columns = self._get_all_columns(table)

            if rows == "ALL":
                cursor.execute(f"SELECT rowid, * FROM {table}")
            else:
                cursor.execute(f"SELECT rowid, * FROM {table} WHERE {rows}")
            rows_data = cursor.fetchall()
            all_columns = self._get_all_columns(table)

            for row in rows_data:
                primary_key_value = row[0]
                encrypted_row = list(row[1:])  # exclude rowid
                encryption_bits = ""

                for i, value in enumerate(encrypted_row):
                    if columns == "ALL" or (isinstance(columns, list) and all_columns[i] in columns):
                        encrypted_value = self._encrypt_data(str(value), password, return_in_base64=save_in_base64)
                        encrypted_row[i] = encrypted_value
                        encryption_bits += "1"
                    else:
                        encryption_bits += "0"

                # Ensure the encryption_bits string is the same length as the number of columns
                while len(encryption_bits) < len(all_columns):
                    encryption_bits += "0"

                encrypted_row.append(encryption_bits)
                placeholders = ', '.join(['?' for _ in encrypted_row])
                cursor.execute(f"UPDATE {table} SET {', '.join([f'{col} = ?' for col in all_columns])}, encrypted = ? WHERE rowid = ?", encrypted_row + [primary_key_value])

        self.conn.commit()

    def decrypt(self, encryption_config: Dict[str, Any]):
        pass


if __name__ == "__main__":
    # Example usage
    db_conn = sqlite3.connect(":memory:")
    secure_db = SecureDatabase(db_conn)

    # Create example table and data
    cursor = db_conn.cursor()
    cursor.execute("CREATE TABLE table1 (column1 TEXT, column2 TEXT, column3 TEXT)")
    cursor.execute("INSERT INTO table1 (column1, column2, column3) VALUES ('value1', 'value2', 'value3')")
    db_conn.commit()

    # Example encryption configuration
    encryption_config = {
        "ALL": "ALL",  # Encrypt all tables and all columns
        "table1": {
            "columns": ["column1", "column2"],  # Columns to encrypt
            "rows": "column3 = 'value3'"  # Row selection criteria
        }
    }

    # Encrypt the database with the given config and password
    secure_db.encrypt(encryption_config, "example_password")

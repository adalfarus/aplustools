from aplustools.security.crypto import CryptUtils
from typing import Dict, Any
import sqlite3


class SecureDatabase:
    def __init__(self, db_connection):
        self.conn = db_connection

    def _get_all_tables(self) -> tuple:
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
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

    @staticmethod
    def _step_through(dic):
        curr_dict = dic
        while True:
            try:
                key, value = next(iter(curr_dict.items()))
                yield key
                curr_dict = value
            except StopIteration:
                 break

    def _get_all(self, levels):
        curr_config = []
        for level in levels:
            curr_config.append(level[0])

        all_getter = [self._get_all_tables, self._get_all_columns, lambda *args: "*"][len(curr_config)]
        return all_getter(*curr_config)

    def _encrypt_data(self, data: str, password: str) -> bytes:
        key = CryptUtils.generate_aes_key(256)
        iv, encrypted_data, tag = CryptUtils.aes_encrypt(data.encode(), key)
        return CryptUtils.pack_ae_data(iv, encrypted_data, tag)

    def encrypt(self, encryption_config: Dict[str, Any], password: str):
        cursor = self.conn.cursor()

        levels = []
        for config in self._step_through(encryption_config):
            if isinstance(config, tuple):
                levels.append(config)
            else:
                levels.append((config,) if config != "ALL" else (self._get_all(levels)))

        print(levels)

        for level in levels:
            if len(level) == 1:
                table_name = level[0]
                self._add_encrypted_column(table_name)
                columns = self._get_all_columns(table_name)
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()

                for row in rows:
                    primary_key_value = row[0]
                    encrypted_row = []
                    encryption_bits = ""

                    for i, value in enumerate(row):
                        if i == 0:
                            encrypted_row.append(value)
                            encryption_bits += "0"
                        else:
                            encrypted_value = self._encrypt_data(str(value), password)
                            encrypted_row.append(encrypted_value)
                            encryption_bits += "1"

                    encrypted_row.append(encryption_bits)
                    placeholders = ', '.join(['?' for _ in encrypted_row])
                    cursor.execute(f"INSERT OR REPLACE INTO {table_name} VALUES ({placeholders})", encrypted_row)
            elif len(level) == 2:
                table_name, column_name = level
                self._add_encrypted_column(table_name)
                cursor.execute(f"SELECT {column_name} FROM {table_name}")
                rows = cursor.fetchall()

                for row in rows:
                    value = row[0]
                    encrypted_value = self._encrypt_data(str(value), password)
                    cursor.execute(f"UPDATE {table_name} SET {column_name} = ? WHERE {column_name} = ?", (encrypted_value, value))

        self.conn.commit()

    def decrypt(self, encryption_config: Dict[str, Any]):
        pass

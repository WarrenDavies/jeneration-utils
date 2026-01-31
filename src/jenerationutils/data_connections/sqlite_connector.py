import sqlite3
import os
from typing import List, Any, Dict
from pathlib import Path
import datetime

import pandas as pd

from jenerationutils.data_connections.base_connector import BaseConnector
from jenerationutils.data_connections.registry import register

@register("sqlite3")
class SQLiteConnector(BaseConnector):
    """
    Concrete connector implementation for SQLite Operations.

    Handles creating new databases and tables and running queries.
    """
    def __init__(self, config):
        """
        Initializes the SQLite connector.

        Args:
            config (dict): Must contain 'data_source_location' (str), which
                           is the file path to the database.
        """
        super().__init__(config)
        self.pydantic_to_sql_map = {
            int: "INTEGER",
            str: "TEXT",
            float: "REAL",
            bool: "BOOLEAN",
            datetime: "TIMESTAMP",
        }
        self.config = config
        self.db_path = self.config["data_source_location"]
        self.db_conn = None


    def generate_create_table_query(self, table_name, schema):
        cols = []
        for name, field in schema.model_fields.items():
            py_type = field.annotation
            sql_type = self.pydantic_to_sql_map.get(py_type, "TEXT")

            col = f"{name} {sql_type}"
            if field.is_required():
                col += " NOT NULL"

            cols.append(col)

        qry = f"""CREATE TABLE IF NOT EXISTS {table_name} (
            {", ".join(cols)}
        );
        """

        return qry

        
    def create_tables_from_schema(self, schema_registry):
        with self.db_conn:  # This ensures the connection is properly managed
            cursor = self.db_conn.cursor()
            for table_name, schema in schema_registry.items():
                qry = self.generate_create_table_query(table_name, schema)
                cursor.execute(qry)


    def create_new_data_source(self):
        conn = sqlite3.connect(self.db_path)
        return conn


    def db_exists(self):
        return Path(self.db_path).exists()


    def ensure_db_exists(self, schema_registry):      
        if self.db_exists():
            self.db_conn = sqlite3.connect(self.db_path)
            return
        self.db_conn = self.create_new_data_source()
        self.create_tables_from_schema(schema_registry)


    def append_data(self, data):
        """
        Appends a row of data to the table indicated in the config.

        Args:
            data (List[Any]): A list of values representing a single row.
                              Order must match the headers.

        Raises:
            FileNotFoundError: If the file at 'data_source_location' does not exist.
            IOError: If there is an issue opening or writing to the file.
        """
        pass


    @staticmethod
    def create_new_data_source_if_not_exists(self, data_sources: Dict[str, str]):
        """
        Creates a new SQLite table specfied in the schemas.

        Args:
            data_sources (Dict[str, str]): Must contain

        Raises:
            FileExistsError: If the file already exists (due to mode 'x').
            IOError: If the file cannot be created.
        """
        path = self.config.get("data_source_location")

        with open(path, "x", newline="", encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)


    def close(self, conn = None):
        """
        Closes connection to database (i.e. if context manager wasn't used).
        """
        try:
            if conn:
                conn.close()
            elif hasattr(self, 'db_conn') and self.db_conn:
                self.db_conn.close()
        except Exception as e:
            print(f"Error closing connection: {e}")


    def to_pandas(self):
        """
        Reads the CSV file specified in the config under 'data_source_location'
        and returns its contents as a Pandas DataFrame.

        Returns:
            pd.DataFrame: DataFrame containing the data from the CSV file.
        """
        path = Path(self.config.get("data_source_location"))

        df = pd.read_csv(path, header=0)

        return df

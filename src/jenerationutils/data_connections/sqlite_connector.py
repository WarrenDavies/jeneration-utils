import sqlite3
import os
from typing import List, Any, Dict
from pathlib import Path
import datetime
import json

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

        
    def create_tables_from_schema(self, conn, schema_registry):

        conn = self.get_connection()

        try:
            cursor = conn.cursor()
            cursor = conn.cursor()
            for table_name, schema in schema_registry.items():
                qry = self.generate_create_table_query(table_name, schema)
                cursor.execute(qry)
        finally:
            cursor.close()
            conn.close()


    def create_new_data_source(self):
        conn = sqlite3.connect(self.db_path)
        return conn


    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn


    def db_exists(self):
        return Path(self.db_path).exists()


    def ensure_db_exists(self, schema_registry):      
        if self.db_exists():
            return
        self.create_tables_from_schema(schema_registry)


    def _get_data_row(self, model, fields):
        values = []
        for field in fields:
            value = getattr(model, field)

            if isinstance(value, dict):
                value = json.dumps(value)
            elif isinstance(value, list):
                value = json.dumps(value)
            elif isinstance(value, datetime.datetime):
                value = value.isoformat()

            values.append(value)

        return values


    def append_data(self, table_name, model):
        """
        Appends a row of data to the table indicated in the config.

        Args:
            table (str): Name of the table into which you want to append the data
            model (BaseModel): Pydantic model containing the record
        """
        fields = list(model.model_fields.keys())
        placeholders = ", ".join(["?"] * len(fields))
        columns = ", ".join(fields)

        values = self._get_data_row(model, fields)

        qry = f"""
        INSERT INTO {table_name} ({columns})
        VALUES ({placeholders})
        """

        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(qry, values)
            conn.commit()
        finally:
            cursor.close()
            conn.close()



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


    def execute(self, qry, args = None):
        if args is None:
            args = ()

        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(qry, args)
            conn.commit()
            rows = [dict(row) for row in cursor.fetchall()]
        finally:
            cursor.close()
            conn.close()

        return rows

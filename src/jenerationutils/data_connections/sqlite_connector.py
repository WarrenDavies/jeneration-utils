import sqlite3
import os
from typing import List, Any
from pathlib import Path

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


    def close():
        """
        Implementation not needed for CSV files.
        """
        pass


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

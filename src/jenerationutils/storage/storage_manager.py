from pathlib import Path
import datetime
import os
import sys
import yaml
import sqlite3

from jenerationutils.data_connections import registry as data_connections_registry


class StorageManager():
    """
    """

    def __init__(self, core_config, experiment_config=None, schema_registry=None):
        self.core_config = core_config
        self.schema_registry = schema_registry
        self.artifacts = []
        self.save_timestamp = ""
        self.filenames = []
        self.pydantic_to_sql_map = {
            int: "INTEGER",
            str: "TEXT",
            float: "REAL",
            bool: "BOOLEAN",
            datetime: "TIMESTAMP",
        }
        self.db_path = self.core_config["data_connection"]["data_source_location"]
        self.db_conn = None
        self.data_connections = {}
        self.create_connections()
        self.ensure_db_exists()


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

        
    def create_tables_from_schema(self):
        cursor = self.db_conn.cursor()
        for table_name, schema in self.schema_registry.items():
            qry = self.generate_create_table_query(table_name, schema)
            cursor.execute(qry)
        self.db_conn.close()


    def create_db(self):
        conn = sqlite3.connect(self.db_path)
        return conn


    def db_exists(self):
        return Path(self.db_path).exists()


    def ensure_db_exists(self):      
        if self.db_exists():
            self.db_conn = sqlite3.connect(self.db_path)
            return
        self.db_conn = self.create_db()
        self.create_tables_from_schema()


    def create_data_connection(self, connection_config):
        connection_name = connection_config["name"]
        self.data_connections[connection_name] = (
            data_connections_registry.get_object(connection_config["data_source"])
        )


    def create_connections(self):
        if "data_connections" not in self.core_config:
            return
        for connection in self.core_config["data_connections"]:
            self.data_connections[connection] = (
                data_connections_registry.get_object(
                    self.core_config["data_connections"][connection]
                )
            )


    def save(self, output_folder, artifacts = None):
        """
        Saves generated artifacts to the configured directory.

        Images are saved with a timestamped filename.
        """
        if not artifacts:
            artifacts = self.artifacts

        save_timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")
        batch_filenames = []
        for i, artifact in enumerate(artifacts):
            generation_no = str((len(self.filenames) + 1)).zfill(4)
            file_name = f"{generation_no}_{save_timestamp}_no{i + 1}{artifact.extension}"
            batch_filenames.append(file_name)
            self.filenames.append(file_name)
            print("saving ", file_name)
            save_path = os.path.join(output_folder, file_name)
            artifact.save(save_path)

        return batch_filenames

    
    def create_data_store(self, headers):
        self.data_connection.create_new_data_source(headers)

    
    def dump_config(self, config, path):
        yaml.safe_dump(config, open(path, "w"))

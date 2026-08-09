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
        self.data_connection = self.create_connection()
        self.data_connection.ensure_db_exists(self.schema_registry)


    def create_connection(self):
        ConnectionClass = data_connections_registry.get_class(
            self.core_config["data_connection"]["output_data_type"]
        )
        return ConnectionClass(self.core_config["data_connection"])


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

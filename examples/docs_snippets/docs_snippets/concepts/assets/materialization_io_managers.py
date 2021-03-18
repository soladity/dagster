import os

import pandas as pd
from dagster import AssetKey, AssetMaterialization, EventMetadataEntry, IOManager


def read_csv(_path):
    return pd.DataFrame()


# start_marker_0
class PandasCsvIOManager(IOManager):
    def load_input(self, context):
        file_path = os.path.join("my_base_dir", context.step_key, context.name)
        return read_csv(file_path)

    def handle_output(self, context, obj):
        file_path = os.path.join("my_base_dir", context.step_key, context.name)

        obj.to_csv(file_path)

        yield AssetMaterialization(
            asset_key=AssetKey(file_path), description="Persisted result to storage."
        )


# end_marker_0


# start_marker_1
class PandasCsvIOManagerWithAsset(IOManager):
    def load_input(self, context):
        file_path = os.path.join("my_base_dir", context.step_key, context.name)
        return read_csv(file_path)

    def handle_output(self, context, obj):
        file_path = os.path.join("my_base_dir", context.step_key, context.name)

        obj.to_csv(file_path)

        yield AssetMaterialization(
            asset_key=AssetKey(file_path),
            description="Persisted result to storage.",
            metadata_entries=[
                EventMetadataEntry.int(obj.shape[0], label="number of rows"),
                EventMetadataEntry.float(obj["some_column"].mean(), "some_column mean"),
            ],
        )


# end_marker_1


# start_asset_def
class PandasCsvIOManagerWithOutputAsset(IOManager):
    def load_input(self, context):
        file_path = os.path.join("my_base_dir", context.step_key, context.name)
        return read_csv(file_path)

    def handle_output(self, context, obj):
        file_path = os.path.join("my_base_dir", context.step_key, context.name)

        obj.to_csv(file_path)

        yield EventMetadataEntry.int(obj.shape[0], label="number of rows")
        yield EventMetadataEntry.float(obj["some_column"].mean(), "some_column mean")

    def get_output_asset_key(self, context):
        file_path = os.path.join("my_base_dir", context.step_key, context.name)
        return AssetKey(file_path)


# end_asset_def

# start_partitioned_asset_def
class PandasCsvIOManagerWithOutputAssetPartitions(IOManager):
    def load_input(self, context):
        file_path = os.path.join("my_base_dir", context.step_key, context.name)
        return read_csv(file_path)

    def handle_output(self, context, obj):
        file_path = os.path.join("my_base_dir", context.step_key, context.name)

        obj.to_csv(file_path)

        yield EventMetadataEntry.int(obj.shape[0], label="number of rows")
        yield EventMetadataEntry.float(obj["some_column"].mean(), "some_column mean")

    def get_output_asset_key(self, context):
        file_path = os.path.join("my_base_dir", context.step_key, context.name)
        return AssetKey(file_path)

    def get_output_asset_partitions(self, context):
        return set(context.config["partitions"])


# end_partitioned_asset_def

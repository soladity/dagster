from dagster import (
    DagsterInstance,
    ModeDefinition,
    OutputDefinition,
    execute_pipeline,
    pipeline,
    repository,
    solid,
)
from dagster.core.definitions.utils import struct_to_string
from dagster.core.execution.api import reexecute_pipeline
from dagster.core.storage.asset_store import custom_path_fs_asset_store


def train(df):
    return len(df)


local_asset_store = custom_path_fs_asset_store.configured(
    {"base_dir": "uncommitted/intermediates/"}
)


@solid(
    output_defs=[
        OutputDefinition(manager_key="fs_asset_store", asset_metadata={"path": "call_api_output"})
    ]
)
def call_api(_):
    return [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]


@solid(
    output_defs=[
        OutputDefinition(manager_key="fs_asset_store", asset_metadata={"path": "parse_df_output"})
    ]
)
def parse_df(context, df):
    context.log.info(struct_to_string(df))
    result_df = df[:5]
    return result_df


@solid(
    output_defs=[
        OutputDefinition(
            manager_key="fs_asset_store", asset_metadata={"path": "train_model_output"}
        )
    ]
)
def train_model(context, df):
    context.log.info(struct_to_string(df))
    model = train(df)
    return model


@pipeline(
    mode_defs=[
        ModeDefinition("test", resource_defs={"fs_asset_store": custom_path_fs_asset_store}),
        ModeDefinition("local", resource_defs={"fs_asset_store": local_asset_store}),
    ]
)
def custom_path_pipeline():
    train_model(parse_df(call_api()))


@repository
def builtin_custom_path_repo():
    return [custom_path_pipeline]


if __name__ == "__main__":
    instance = DagsterInstance.ephemeral()
    result = execute_pipeline(custom_path_pipeline, mode="local", instance=instance)
    reexecute_pipeline(
        custom_path_pipeline,
        result.run_id,
        mode="local",
        instance=instance,
        step_selection=["parse_df*"],
    )

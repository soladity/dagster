import json
import time
from typing import Callable, Iterator, Optional

import pandas as pd
from dagster_pandas import DataFrame

from dagster import (
    Array,
    AssetMaterialization,
    Bool,
    EventMetadataEntry,
    Failure,
    Field,
    InputDefinition,
    Int,
    Noneable,
    Nothing,
    Output,
    OutputDefinition,
    Permissive,
    RetryRequested,
    String,
    check,
    solid,
)

from .types import DbtRpcPollResult
from .utils import log_rpc, raise_for_rpc_error


def generate_materializations(rpc_poll_result: DbtRpcPollResult) -> Iterator[AssetMaterialization]:
    for node_result in rpc_poll_result.results:
        if node_result.node["resource_type"] in ["model", "snapshot"]:
            success = not node_result.fail and not node_result.skip and not node_result.error
            if success:
                entries = [
                    EventMetadataEntry.json(data=node_result.node, label="Node"),
                    EventMetadataEntry.text(text=node_result.status, label="Status"),
                    EventMetadataEntry.text(
                        text=str(node_result.execution_time), label="Execution Time"
                    ),
                    EventMetadataEntry.text(
                        text=node_result.node["config"]["materialized"],
                        label="Materialization Strategy",
                    ),
                    EventMetadataEntry.text(text=node_result.node["database"], label="Database"),
                    EventMetadataEntry.text(text=node_result.node["schema"], label="Schema"),
                    EventMetadataEntry.text(text=node_result.node["alias"], label="Alias"),
                    EventMetadataEntry.text(
                        text=node_result.node["description"], label="Description"
                    ),
                ]
                for node_timing in node_result.timing:
                    if node_timing.name == "execute":
                        execution_entries = [
                            EventMetadataEntry.text(
                                text=node_timing.started_at.isoformat(timespec="seconds"),
                                label="Execution Started At",
                            ),
                            EventMetadataEntry.text(
                                text=node_timing.completed_at.isoformat(timespec="seconds"),
                                label="Execution Completed At",
                            ),
                            EventMetadataEntry.text(
                                text=str(node_timing.duration), label="Execution Duration"
                            ),
                        ]
                        entries.extend(execution_entries)
                    if node_timing.name == "compile":
                        execution_entries = [
                            EventMetadataEntry.text(
                                text=node_timing.started_at.isoformat(timespec="seconds"),
                                label="Compilation Started At",
                            ),
                            EventMetadataEntry.text(
                                text=node_timing.completed_at.isoformat(timespec="seconds"),
                                label="Compilation Completed At",
                            ),
                            EventMetadataEntry.text(
                                text=str(node_timing.duration), label="Compilation Duration"
                            ),
                        ]
                        entries.extend(execution_entries)

                yield AssetMaterialization(
                    description="A materialized node within the dbt graph.",
                    metadata_entries=entries,
                    asset_key=node_result.node["unique_id"],
                )


def dbt_rpc_poll(
    context, request_token: str, should_yield_materializations: bool = True
) -> DbtRpcPollResult:

    resp = context.resources.dbt_rpc.poll(
        request_token=request_token, logs=context.solid_config["logs"]
    )
    raise_for_rpc_error(context, resp)

    interval = context.solid_config["interval"]
    logs_start = 0
    while resp.json().get("result").get("state") == "running":
        context.log.debug(
            f"Request {request_token} currently in state '{resp.json().get('result').get('state')}' (elapsed time {resp.json().get('result').get('elapsed', 0)} seconds). Sleeping for {interval}s.."
        )

        if context.solid_config["logs"]:
            logs = resp.json().get("result").get("logs")
            if len(logs) > 0:
                log_rpc(context, logs)
            logs_start += len(logs)

        time.sleep(interval)
        resp = context.resources.dbt_rpc.poll(
            request_token=request_token, logs=context.solid_config["logs"], logs_start=logs_start
        )
        raise_for_rpc_error(context, resp)

    if resp.json().get("result").get("state") != "success":
        if context.solid_config["logs"]:
            logs = resp.json().get("result").get("logs")
            if len(logs) > 0:
                log_rpc(context, logs)

        raise Failure(
            description=f"Request {request_token} finished with state '{resp.json().get('result').get('state')}' in {resp.json().get('result').get('elapsed')} seconds",
        )

    else:
        context.log.info(
            f"Request {request_token} finished with state '{resp.json().get('result').get('state')}' in {resp.json().get('result').get('elapsed')} seconds"
        )

    if context.solid_config["logs"]:
        logs = resp.json().get("result").get("logs")
        if len(logs) > 0:
            log_rpc(context, logs)

    context.log.debug(json.dumps(resp.json().get("result"), indent=2))
    rpc_poll_result = DbtRpcPollResult.from_results(resp.json().get("result"))
    if should_yield_materializations:
        for materialization in generate_materializations(rpc_poll_result=rpc_poll_result):
            yield materialization
    yield Output(value=rpc_poll_result, output_name="result")


@solid(
    description="A solid to invoke dbt run over RPC.",
    input_defs=[InputDefinition(name="start_after", dagster_type=Nothing)],
    output_defs=[
        OutputDefinition(
            name="request_token",
            dagster_type=String,
            description="The request token of the invoked dbt run.",
        )
    ],
    config_schema={
        "models": Field(
            config=Noneable(Array(String)),
            default_value=None,
            is_required=False,
            description="The dbt models to run.",
        ),
        "exclude": Field(
            config=Noneable(Array(String)),
            default_value=None,
            is_required=False,
            description="The dbt models to exclude.",
        ),
    },
    required_resource_keys={"dbt_rpc"},
    tags={"kind": "dbt"},
)
def dbt_rpc_run(context) -> String:
    resp = context.resources.dbt_rpc.run(
        models=context.solid_config["models"], exclude=context.solid_config["exclude"]
    )
    context.log.debug(resp.text)
    raise_for_rpc_error(context, resp)
    return resp.json().get("result").get("request_token")


@solid(
    description="A solid to invoke dbt run over RPC and poll the resulting RPC process until it's complete.",
    input_defs=[InputDefinition(name="start_after", dagster_type=Nothing)],
    output_defs=[OutputDefinition(name="result", dagster_type=DbtRpcPollResult)],
    config_schema={
        "models": Field(
            config=Noneable(Array(String)),
            default_value=None,
            is_required=False,
            description="The dbt models to run.",
        ),
        "exclude": Field(
            config=Noneable(Array(String)),
            default_value=None,
            is_required=False,
            description="The dbt models to exclude.",
        ),
        "full_refresh": Field(
            config=Bool,
            description="Whether or not to perform a --full-refresh.",
            is_required=False,
            default_value=False,
        ),
        "fail_fast": Field(
            config=Bool,
            description="Whether or not to --fail-fast.",
            is_required=False,
            default_value=False,
        ),
        "warn_error": Field(
            config=Bool,
            description="Whether or not to --warn-error.",
            is_required=False,
            default_value=False,
        ),
        "interval": Field(
            config=Int,
            is_required=False,
            default_value=10,
            description="The interval (in seconds) at which to poll the dbt rpc process.",
        ),
        "logs": Field(
            config=Bool,
            is_required=False,
            default_value=True,
            description="Whether or not to return logs from the process.",
        ),
        "task_tags": Permissive(),
        "max_retries": Field(config=Int, is_required=False, default_value=5),
        "retry_interval": Field(config=Int, is_required=False, default_value=120),
    },
    required_resource_keys={"dbt_rpc"},
    tags={"kind": "dbt"},
)
def dbt_rpc_run_and_wait(context) -> DbtRpcPollResult:

    if context.solid_config["task_tags"]:
        results = context.resources.dbt_rpc.ps().json()
        for task in results["result"]["rows"]:
            if task["tags"] == context.solid_config["task_tags"]:
                context.log.warning(
                    f"RPC task with tags {json.dumps(task['tags'])} currently running."
                )
                raise RetryRequested(
                    max_retries=context.solid_config["max_retries"],
                    seconds_to_wait=context.solid_config["retry_interval"],
                )

    command = ""

    if context.solid_config["warn_error"]:
        command += " --warn-error"

    command += " run"

    if context.solid_config["models"]:
        models = " ".join(set(context.solid_config["models"]))
        command += f" --models {models}"

    if context.solid_config["exclude"]:
        exclude = " ".join(set(context.solid_config["exclude"]))
        command += f" --exclude {exclude}"

    if context.solid_config["full_refresh"]:
        command += " --full-refresh"

    if context.solid_config["fail_fast"]:
        command += " --fail-fast"

    context.log.debug(f"Running dbt command: dbt {command}")
    resp = context.resources.dbt_rpc.cli(cli=command, **context.solid_config["task_tags"])
    context.log.debug(resp.text)
    raise_for_rpc_error(context, resp)
    request_token = resp.json().get("result").get("request_token")
    return dbt_rpc_poll(context, request_token)


@solid(
    description="A solid to invoke dbt test over RPC.",
    input_defs=[InputDefinition(name="start_after", dagster_type=Nothing)],
    output_defs=[
        OutputDefinition(
            name="request_token",
            dagster_type=String,
            description="The request token of the invoked dbt test.",
        )
    ],
    config_schema={
        "models": Field(
            config=Noneable(Array(String)),
            default_value=None,
            is_required=False,
            description="The dbt models to test.",
        ),
        "exclude": Field(
            config=Noneable(Array(String)),
            default_value=None,
            is_required=False,
            description="The dbt models to exclude.",
        ),
        "data": Field(
            config=Bool,
            default_value=True,
            is_required=False,
            description="Whether or not to run custom data tests.",
        ),
        "schema": Field(
            config=Bool,
            default_value=True,
            is_required=False,
            description="Whether or not to run schema tests.",
        ),
    },
    required_resource_keys={"dbt_rpc"},
    tags={"kind": "dbt"},
)
def dbt_rpc_test(context) -> String:
    resp = context.resources.dbt_rpc.test(
        models=context.solid_config["models"],
        exclude=context.solid_config["exclude"],
        data=context.solid_config["data"],
        schema=context.solid_config["schema"],
    )
    context.log.debug(resp.text)
    raise_for_rpc_error(context, resp)
    return resp.json().get("result").get("request_token")


@solid(
    description="A solid to invoke dbt test over RPC and poll the resulting RPC process until it's complete.",
    input_defs=[InputDefinition(name="start_after", dagster_type=Nothing)],
    output_defs=[OutputDefinition(name="result", dagster_type=DbtRpcPollResult)],
    config_schema={
        "models": Field(
            config=Noneable(Array(String)),
            default_value=None,
            is_required=False,
            description="The dbt models to test.",
        ),
        "exclude": Field(
            config=Noneable(Array(String)),
            default_value=None,
            is_required=False,
            description="The dbt models to exclude.",
        ),
        "data": Field(
            config=Bool,
            default_value=True,
            is_required=False,
            description="Whether or not to run custom data tests.",
        ),
        "schema": Field(
            config=Bool,
            default_value=True,
            is_required=False,
            description="Whether or not to run schema tests.",
        ),
        "interval": Field(
            config=Int,
            is_required=False,
            default_value=10,
            description="The interval (in seconds) at which to poll the dbt rpc process.",
        ),
        "logs": Field(
            config=Bool,
            is_required=False,
            default_value=True,
            description="Whether or not to return logs from the process.",
        ),
    },
    required_resource_keys={"dbt_rpc"},
    tags={"kind": "dbt"},
)
def dbt_rpc_test_and_wait(context) -> DbtRpcPollResult:
    resp = context.resources.dbt_rpc.test(
        models=context.solid_config["models"],
        exclude=context.solid_config["exclude"],
        data=context.solid_config["data"],
        schema=context.solid_config["schema"],
    )
    context.log.debug(resp.text)
    raise_for_rpc_error(context, resp)
    request_token = resp.json().get("result").get("request_token")
    return dbt_rpc_poll(context, request_token)


@solid(
    description="A solid to invoke a dbt run operation over RPC.",
    input_defs=[InputDefinition(name="start_after", dagster_type=Nothing)],
    output_defs=[
        OutputDefinition(
            name="request_token",
            dagster_type=String,
            description="The request token of the invoked dbt run operation.",
        )
    ],
    config_schema={
        "macro": Field(
            config=String,
            is_required=True,
            description="The dbt macro to invoke as a run operation",
        ),
        "args": Field(
            config=Noneable(Permissive()),
            is_required=False,
            default_value=None,
            description="Arguments to supply to the invoked macro.",
        ),
    },
    required_resource_keys={"dbt_rpc"},
    tags={"kind": "dbt"},
)
def dbt_rpc_run_operation(context) -> String:
    resp = context.resources.dbt_rpc.run_operation(
        macro=context.solid_config["macro"], args=context.solid_config["args"]
    )
    context.log.debug(resp.text)
    raise_for_rpc_error(context, resp)
    return resp.json().get("result").get("request_token")


@solid(
    description="A solid to invoke a dbt run operation over RPC and poll the resulting RPC process until it's complete.",
    input_defs=[InputDefinition(name="start_after", dagster_type=Nothing)],
    output_defs=[OutputDefinition(name="result", dagster_type=DbtRpcPollResult)],
    config_schema={
        "macro": Field(
            config=String,
            is_required=True,
            description="The dbt macro to invoke as a run operation",
        ),
        "args": Field(
            config=Noneable(Permissive()),
            is_required=False,
            default_value=None,
            description="Arguments to supply to the invoked macro.",
        ),
        "interval": Field(
            config=Int,
            is_required=False,
            default_value=10,
            description="The interval (in seconds) at which to poll the dbt rpc process.",
        ),
        "logs": Field(
            config=Bool,
            is_required=False,
            default_value=True,
            description="Whether or not to return logs from the process.",
        ),
    },
    required_resource_keys={"dbt_rpc"},
    tags={"kind": "dbt"},
)
def dbt_rpc_run_operation_and_wait(context) -> DbtRpcPollResult:
    resp = context.resources.dbt_rpc.run_operation(
        macro=context.solid_config["macro"], args=context.solid_config["args"]
    )
    context.log.debug(resp.text)
    raise_for_rpc_error(context, resp)
    request_token = resp.json().get("result").get("request_token")
    return dbt_rpc_poll(context, request_token)


@solid(
    description="A solid to invoke a dbt snapshot over RPC.",
    input_defs=[InputDefinition(name="start_after", dagster_type=Nothing)],
    output_defs=[
        OutputDefinition(
            name="request_token",
            dagster_type=String,
            description="The request token of the invoked dbt snapshot.",
        )
    ],
    config_schema={
        "select": Field(
            config=Noneable(Array(String)),
            default_value=None,
            is_required=False,
            description="The dbt snapshot files to snapshot.",
        ),
        "exclude": Field(
            config=Noneable(Array(String)),
            default_value=None,
            is_required=False,
            description="The dbt snapshot files to exclude from the snapshot.",
        ),
    },
    required_resource_keys={"dbt_rpc"},
    tags={"kind": "dbt"},
)
def dbt_rpc_snapshot(context) -> String:
    resp = context.resources.dbt_rpc.snapshot(
        select=context.solid_config["select"], exclude=context.solid_config["exclude"]
    )
    context.log.debug(resp.text)
    raise_for_rpc_error(context, resp)
    return resp.json().get("result").get("request_token")


@solid(
    description="A solid to invoke a dbt snapshot over RPC and poll the resulting RPC process until it's complete.",
    input_defs=[InputDefinition(name="start_after", dagster_type=Nothing)],
    output_defs=[OutputDefinition(name="result", dagster_type=DbtRpcPollResult)],
    config_schema={
        "select": Field(
            config=Noneable(Array(String)),
            default_value=None,
            is_required=False,
            description="The dbt snapshot files to snapshot.",
        ),
        "exclude": Field(
            config=Noneable(Array(String)),
            default_value=None,
            is_required=False,
            description="The dbt snapshot files to exclude from the snapshot.",
        ),
        "interval": Field(
            config=Int,
            is_required=False,
            default_value=10,
            description="The interval (in seconds) at which to poll the dbt rpc process.",
        ),
        "logs": Field(
            config=Bool,
            is_required=False,
            default_value=True,
            description="Whether or not to return logs from the process.",
        ),
        "task_tags": Permissive(),
        "max_retries": Field(config=Int, is_required=False, default_value=5),
        "retry_interval": Field(config=Int, is_required=False, default_value=120),
    },
    required_resource_keys={"dbt_rpc"},
    tags={"kind": "dbt"},
)
def dbt_rpc_snapshot_and_wait(context) -> DbtRpcPollResult:

    if context.solid_config["task_tags"]:
        results = context.resources.dbt_rpc.ps().json()
        for task in results["result"]["rows"]:
            if task["tags"] == context.solid_config["task_tags"]:
                context.log.warning(
                    f"RPC task with tags {json.dumps(task['tags'])} currently running."
                )
                raise RetryRequested(
                    max_retries=context.solid_config["max_retries"],
                    seconds_to_wait=context.solid_config["retry_interval"],
                )

    resp = context.resources.dbt_rpc.snapshot(
        select=context.solid_config["select"], exclude=context.solid_config["exclude"]
    )
    context.log.debug(resp.text)
    raise_for_rpc_error(context, resp)
    request_token = resp.json().get("result").get("request_token")
    return dbt_rpc_poll(context, request_token)


@solid(
    description="A solid to invoke dbt source snapshot-freshness over RPC.",
    input_defs=[InputDefinition(name="start_after", dagster_type=Nothing)],
    output_defs=[
        OutputDefinition(
            name="request_token",
            dagster_type=String,
            description="The request token of the invoked dbt snapshot.",
        )
    ],
    config_schema={
        "select": Field(
            config=Noneable(Array(String)),
            default_value=None,
            is_required=False,
            description="The dbt sources to snapshot-freshness for.",
        ),
        "warn_error": Field(
            config=Bool,
            description="Whether or not to --warn-error.",
            is_required=False,
            default_value=False,
        ),
    },
    required_resource_keys={"dbt_rpc"},
    tags={"kind": "dbt"},
)
def dbt_rpc_snapshot_freshness(context) -> String:
    command = ""

    if context.solid_config["warn_error"]:
        command += " --warn-error"

    command += " source snapshot-freshness"

    if context.solid_config["select"]:
        select = " ".join(set(context.solid_config["select"]))
        command += f" --select {select}"

    context.log.debug(f"Running dbt command: dbt {command}")
    resp = context.resources.dbt_rpc.cli(cli=command)
    context.log.debug(resp.text)
    raise_for_rpc_error(context, resp)
    return resp.json().get("result").get("request_token")


@solid(
    description="A solid to invoke dbt source snapshot-freshness over RPC and poll the resulting RPC process until it's complete.",
    input_defs=[InputDefinition(name="start_after", dagster_type=Nothing)],
    output_defs=[OutputDefinition(name="result", dagster_type=DbtRpcPollResult)],
    config_schema={
        "select": Field(
            config=Noneable(Array(String)),
            default_value=None,
            is_required=False,
            description="The dbt sources to snapshot-freshness for.",
        ),
        "warn_error": Field(
            config=Bool,
            description="Whether or not to --warn-error.",
            is_required=False,
            default_value=False,
        ),
        "interval": Field(
            config=Int,
            is_required=False,
            default_value=10,
            description="The interval (in seconds) at which to poll the dbt rpc process.",
        ),
        "logs": Field(
            config=Bool,
            is_required=False,
            default_value=True,
            description="Whether or not to return logs from the process.",
        ),
    },
    required_resource_keys={"dbt_rpc"},
    tags={"kind": "dbt"},
)
def dbt_rpc_snapshot_freshness_and_wait(context) -> DbtRpcPollResult:
    command = ""

    if context.solid_config["warn_error"]:
        command += " --warn-error"

    command += " source snapshot-freshness"

    if context.solid_config["select"]:
        select = " ".join(set(context.solid_config["select"]))
        command += f" --select {select}"

    context.log.debug(f"Running dbt command: dbt {command}")
    resp = context.resources.dbt_rpc.cli(cli=command)
    context.log.debug(resp.text)
    raise_for_rpc_error(context, resp)
    request_token = resp.json().get("result").get("request_token")
    return dbt_rpc_poll(context, request_token)


@solid(
    description="A solid to compile a SQL query in context of a dbt project over RPC.",
    input_defs=[
        InputDefinition(name="start_after", dagster_type=Nothing),
        InputDefinition(
            name="sql", description="The SQL query to be compiled.", dagster_type=String
        ),
    ],
    output_defs=[
        OutputDefinition(name="sql", description="The compiled SQL query.", dagster_type=String)
    ],
    config_schema={
        "name": Field(config=String),
        "interval": Field(
            config=Int,
            is_required=False,
            default_value=10,
            description="The interval (in seconds) at which to poll the dbt rpc process.",
        ),
        "logs": Field(
            config=Bool,
            is_required=False,
            default_value=True,
            description="Whether or not to return logs from the process.",
        ),
    },
    required_resource_keys={"dbt_rpc"},
    tags={"kind": "dbt"},
)
def dbt_rpc_compile_sql(context, sql: String) -> String:
    resp = context.resources.dbt_rpc.compile_sql(sql=sql, name=context.solid_config["name"])
    context.log.debug(resp.text)
    raise_for_rpc_error(context, resp)
    request_token = resp.json().get("result").get("request_token")
    result = dbt_rpc_poll(context, request_token)
    return result.results[0].node["compiled_sql"]  # pylint: disable=no-member # TODO


def create_dbt_rpc_run_sql_solid(
    name: str, output_def: Optional[OutputDefinition] = None, **kwargs
) -> Callable:
    """This function is a factory which constructs a solid that will copy the results of a SQL query run within the context of a dbt project to a DataFrame.

    Any kwargs passed to this function will be passed along to the underlying @solid decorator.
    However, note that overriding config, input_defs, and required_resource_keys is not supported. You might consider using
    @composite_solid to wrap this solid in the cases where you'd like to configure the solid
    with different config fields.

    Args:
        name (str): The name of this solid.
        output_def (OutputDefinition, optional): The OutputDefinition for the solid. This value should always be a representation
            of a pandas DataFrame. If not specificed, the solid will default to an OutputDefinition named "df" with a DataFrame dagster type.

    Returns:
        SolidDefinition: Returns the constructed solid definition.
    """
    check.str_param(obj=name, param_name="name")
    check.opt_inst_param(obj=output_def, param_name="output_def", ttype=OutputDefinition)
    check.param_invariant(
        "input_defs" not in kwargs, "input_defs", "Overriding input_defs is not supported."
    )
    check.param_invariant(
        "required_resource_keys" not in kwargs,
        "required_resource_keys",
        "Overriding required_resource_keys is not supported.",
    )

    @solid(
        name=name,
        description=kwargs.pop(
            "description",
            "A solid to run a SQL query in context of a dbt project over RPC and return the results in a pandas DataFrame.",
        ),
        input_defs=[
            InputDefinition(name="start_after", dagster_type=Nothing),
            InputDefinition(
                name="sql", description="The SQL query to be run.", dagster_type=String
            ),
        ],
        output_defs=[
            output_def
            or OutputDefinition(
                name="df", description="The results of the SQL query.", dagster_type=DataFrame
            )
        ],
        config_schema={
            "name": Field(config=String),
            "interval": Field(
                config=Int,
                is_required=False,
                default_value=10,
                description="The interval (in seconds) at which to poll the dbt rpc process.",
            ),
            "logs": Field(
                config=Bool,
                is_required=False,
                default_value=True,
                description="Whether or not to return logs from the process.",
            ),
        },
        required_resource_keys={"dbt_rpc"},
        tags={"kind": "dbt"},
        **kwargs,
    )
    def _dbt_rpc_run_sql(context, sql: String) -> DataFrame:
        resp = context.resources.dbt_rpc.run_sql(sql=sql, name=context.solid_config["name"])
        context.log.debug(resp.text)
        raise_for_rpc_error(context, resp)
        request_token = resp.json().get("result").get("request_token")
        result = dbt_rpc_poll(context, request_token)
        table = result.results[0].table  # pylint: disable=no-member  # TODO
        return pd.DataFrame.from_records(data=table["rows"], columns=table["column_names"])

    return _dbt_rpc_run_sql

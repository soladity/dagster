dbt (dagster-dbt)
-----------------

This library provides a Dagster integration with `dbt <https://getdbt.com/>`_ (data build tool), created by `dbt Labs <https://www.getdbt.com/>`_.

.. currentmodule:: dagster_dbt

Ops
===

``dagster_dbt`` provides a set of pre-built ops that work with either the CLI or RPC interfaces. For
more advanced use cases, we suggest building your own ops which directly interact with these resources.

.. autofunction:: dbt_run_op

.. autofunction:: dbt_compile_op

.. autofunction:: dbt_test_op

.. autofunction:: dbt_snapshot_op

.. autofunction:: dbt_seed_op

.. autofunction:: dbt_docs_generate_op


Resources
=========

CLI
~~~

.. autoclass:: DbtCliResource
    :members:

.. autoclass:: DbtCliOutput
    :members:

.. autodata:: dbt_cli_resource
    :annotation: ResourceDefinition


RPC
~~~

.. autoclass:: DbtRpcClient
    :members:

.. autoclass:: DbtRpcOutput
    :members:

.. autodata:: local_dbt_rpc_resource
    :annotation: ResourceDefinition

.. autodata:: dbt_rpc_resource
    :annotation: ResourceDefinition

.. autodata:: dbt_rpc_sync_resource
    :annotation: ResourceDefinition


Types
=====

.. autoclass:: DbtOutput
    :members:

.. autoclass:: DbtResource
    :members:

Errors
======

.. autoexception:: DagsterDbtError

.. autoexception:: DagsterDbtCliRuntimeError

.. autoexception:: DagsterDbtCliFatalRuntimeError

.. autoexception:: DagsterDbtCliHandledRuntimeError

.. autoexception:: DagsterDbtCliOutputsNotFoundError

.. autoexception:: DagsterDbtCliUnexpectedOutputError

.. autoexception:: DagsterDbtRpcUnexpectedPollOutputError

Solids [Legacy]
===============

dagster_dbt provides a set of solids that may be used in legacy pipelines.

CLI
~~~

.. autofunction:: dbt_cli_compile

.. autofunction:: dbt_cli_run

.. autofunction:: dbt_cli_run_operation

.. autofunction:: dbt_cli_snapshot

.. autofunction:: dbt_cli_snapshot_freshness

.. autofunction:: dbt_cli_test

RPC
~~~

.. autofunction:: create_dbt_rpc_run_sql_solid

.. autofunction:: dbt_rpc_compile_sql

.. autofunction:: dbt_rpc_run

.. autofunction:: dbt_rpc_run_and_wait

.. autofunction:: dbt_rpc_run_operation

.. autofunction:: dbt_rpc_run_operation_and_wait

.. autofunction:: dbt_rpc_snapshot

.. autofunction:: dbt_rpc_snapshot_and_wait

.. autofunction:: dbt_rpc_snapshot_freshness

.. autofunction:: dbt_rpc_snapshot_freshness_and_wait

.. autofunction:: dbt_rpc_test

.. autofunction:: dbt_rpc_test_and_wait
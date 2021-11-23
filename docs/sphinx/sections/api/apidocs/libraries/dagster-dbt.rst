dbt (dagster-dbt)
-----------------

This library provides a Dagster integration with `dbt <https://getdbt.com/>`_ (data build tool), created by `dbt Labs <https://www.getdbt.com/>`_.

.. currentmodule:: dagster_dbt

Ops
===

dbt Core Ops
~~~~~~~~~~~~

``dagster_dbt`` provides a set of pre-built ops that work with either the CLI or RPC interfaces. For
more advanced use cases, we suggest building your own ops which directly interact with these resources.

.. autoconfigurable:: dbt_run_op

.. autofunction:: dbt_compile_op

.. autofunction:: dbt_ls_op

.. autofunction:: dbt_test_op

.. autofunction:: dbt_snapshot_op

.. autofunction:: dbt_seed_op

.. autofunction:: dbt_docs_generate_op

dbt Cloud Ops
~~~~~~~~~~~~~

.. autoconfigurable:: dbt_cloud_run_op

Resources
=========

CLI Resources
~~~~~~~~~~~~~

.. autoclass:: DbtCliResource
    :members:

.. autoclass:: DbtCliOutput
    :members:

.. autoconfigurable:: dbt_cli_resource
    :annotation: ResourceDefinition


RPC Resources
~~~~~~~~~~~~~

.. autoclass:: DbtRpcResource
    :members:

.. autoclass:: DbtRpcSyncResource
    :members:

.. autoclass:: DbtRpcOutput
    :members:

.. autodata:: local_dbt_rpc_resource
    :annotation: ResourceDefinition

.. autoconfigurable:: dbt_rpc_resource
    :annotation: ResourceDefinition

.. autoconfigurable:: dbt_rpc_sync_resource
    :annotation: ResourceDefinition

dbt Cloud Resources
~~~~~~~~~~~~~~~~~~~

.. autoclass:: DbtCloudResourceV2
    :members:

.. autoconfigurable:: dbt_cloud_resource
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

Utils
=====

.. currentmodule:: dagster_dbt.utils

.. autofunction:: generate_materializations

Solids [Legacy]
===============

dagster_dbt provides a set of solids that may be used in legacy pipelines.

CLI Solids
~~~~~~~~~~

.. currentmodule:: dagster_dbt

.. autoconfigurable:: dbt_cli_compile

.. autoconfigurable:: dbt_cli_run

.. autoconfigurable:: dbt_cli_run_operation

.. autoconfigurable:: dbt_cli_snapshot

.. autoconfigurable:: dbt_cli_snapshot_freshness

.. autoconfigurable:: dbt_cli_test

RPC Solids
~~~~~~~~~~

.. autofunction:: create_dbt_rpc_run_sql_solid

.. autoconfigurable:: dbt_rpc_compile_sql

.. autoconfigurable:: dbt_rpc_run

.. autoconfigurable:: dbt_rpc_run_and_wait

.. autoconfigurable:: dbt_rpc_run_operation

.. autoconfigurable:: dbt_rpc_run_operation_and_wait

.. autoconfigurable:: dbt_rpc_snapshot

.. autoconfigurable:: dbt_rpc_snapshot_and_wait

.. autoconfigurable:: dbt_rpc_snapshot_freshness

.. autoconfigurable:: dbt_rpc_snapshot_freshness_and_wait

.. autoconfigurable:: dbt_rpc_test

.. autoconfigurable:: dbt_rpc_test_and_wait
# Introduction

When new releases include breaking changes or deprecations, this document describes how to migrate.

# Migrating to 0.11.0

### Action Required: Run and event storage schema changes

Run this after migrating to 0.11.0:

```
dagster instance migrate
```

This release includes several schema changes to the Dagster storages that improve performance, allow support for MySQL, and enable new features like asset tags and reliable backfills. After upgrading to 0.11.0, run the `dagster instance migrate` command to migrate your instance storage to the latest schema.

### Action Required: Schedule timezones

Schedules now run in UTC (instead of the system timezone) if no timezone has been set on the schedule. If you’re using a deprecated scheduler like `SystemCronScheduler` or `K8sScheduler`, we recommend that you switch to the native Dagster scheduler. The deprecated schedulers will be removed in the next Dagster release.

### Action Required: Asset storage

If upgrading directly to `0.11.0` from `0.9.22` or lower, you might notice some asset keys missing from the catalog if they have not been materialized using a version `0.9.16` or greater.  We removed some back-compatibility for performance reasons.  If this is the case, you can either run `dagster instance reindex` or execute the appropriate pipelines to materialize those assets again.  In either case, the full history of the asset will still be maintained.

### Removals of Deprecated APIs

* The `instance` argument to `RunLauncher.launch_run` has been removed. If you have written a custom RunLauncher, you’ll need to update the signature of that method. You can still access the `DagsterInstance` on the `RunLauncher` via the `_instance` parameter.
* The `has_config_entry`, `has_configurable_inputs`, and `has_configurable_outputs` properties of `solid` and `composite_solid` have been removed.
* The deprecated optionality of the `name` argument to `PipelineDefinition` has been removed, and the argument is now required.
* The `execute_run_with_structured_logs` and `execute_step_with_structured_logs` internal CLI entry points have been removed. Use `execute_run` or `execute_step` instead.
* The `python_environment` key has been removed from `workspace.yaml`. Instead, to specify that a repository location should use a custom python environment, set the `executable_path` key within a `python_file`, `python_module`, or `python_package` key. See [the docs](http://docs.dagster.io/[concepts/repositories-workspaces/workspaces](https://docs.dagster.io/concepts/repositories-workspaces/workspaces)) for more information on configuring your `workspace.yaml` file.
* [dagster-dask] The deprecated schema for reading or materializing dataframes has been removed. Use the `read` or `to` keys accordingly.

### Breaking Changes

* Names provided to `alias` on solids now enforce the same naming rules as solids. You may have to update provided names to meet these requirements.
* The `retries` method on `Executor` should now return a `RetryMode` instead of a `Retries`. This will only affect custom `Executor` classes.
* Submitting partition backfills in Dagit now requires `dagster-daemon` to be running.  The instance setting in `dagster.yaml` to optionally enable daemon-based backfills has been removed, because all backfills are now daemon-based backfills.
```
# removed, no longer a valid setting in dagster.yaml
    backfill:
      daemon_enabled: true
```
The corresponding value flag `dagsterDaemon.backfill.enabled` has also been removed from the Dagster helm chart.

* The sensor daemon interval settings in `dagster.yaml` has been removed.  The sensor daemon now runs in a continuous loop so this customization is no longer useful.
```
# removed, no longer a valid setting in dagster.yaml
    sensor_settings:
      interval_seconds: 10
```

# Migrating to 0.10.0

## Action Required: Run and event storage schema changes

```bash
# Run after migrating to 0.10.0

$ dagster instance migrate
```

This release includes several schema changes to the Dagster storages that improve performance and
enable new features like sensors and run queueing. After upgrading to 0.10.0, run the
`dagster instance migrate` command to migrate your instance storage to the latest schema. This will
turn off any running schedules, so you will need to restart any previously running schedules after
migrating the schema. Before turning them back on, you should follow the steps below to migrate
to `DagsterDaemonScheduler`.

## New scheduler: `DagsterDaemonScheduler`

This release includes a new `DagsterDaemonScheduler` with improved fault tolerance and full support
for timezones. We highly recommend upgrading to the new scheduler during this release. The existing
schedulers, `SystemCronScheduler` and `K8sScheduler`, are deprecated and will be removed in a
future release.

### Steps to migrate

Instead of relying on system cron or k8s cron jobs, the `DaemonScheduler` uses the new
`dagster-daemon` service to run schedules. This requires running the `dagster-daemon` service as a
part of your deployment.

Refer to our [deployment documentation](https://docs.dagster.io/deploying) for a guides on how to
set up and run the daemon process for local development, Docker, or Kubernetes deployments.

**If you are currently using the SystemCronScheduler or K8sScheduler:**

1. Stop any currently running schedules, to prevent any dangling cron jobs from being left behind.
   You can do this through the Dagit UI, or using the following command:

    ```bash
    dagster schedule stop --location {repository_location_name} {schedule_name}
    ```

    If you do not stop running schedules before changing schedulers, Dagster will throw an exception
    on startup due to the misconfigured running schedules.

2. In your `dagster.yaml` file, remove the `scheduler:` entry. If there is no `scheduler:` entry,
   the `DagsterDaemonScheduler` is automatically used as the default scheduler.

3. Start the `dagster-daemon` process. Guides can be found in our
   [deployment documentations](https://docs.dagster.io/deploying).

See our [schedules troubleshooting guide](https://docs.dagster.io/troubleshooting/schedules) for
help if you experience any problems with the new scheduler.

**If you are not using a legacy scheduler:**

No migration steps are needed, but make sure you run `dagster instance migrate` as a part of
upgrading to 0.10.0.

## Deprecation: Intermediate Storage

We have deprecated the intermediate storage machinery in favor of the new IO manager abstraction,
which offers finer-grained control over how inputs and outputs are serialized and persisted. Check
out the [IO Managers Overview](https://docs.dagster.io/0.10.0/overview/io-managers/io-managers) for
more information.

### Steps to Migrate

* We have deprecated the top level `"storage"` and `"intermediate_storage"` fields on `run_config`.
  If you are currently executing pipelines as follows:

    ```python
    @pipeline
    def my_pipeline():
        ...

    execute_pipeline(
        my_pipeline,
        run_config={
            "intermediate_storage": {
                "filesystem": {"base_dir": ...}
            }
        },
    )

    execute_pipeline(
        my_pipeline,
        run_config={
            "storage": {
                "filesystem": {"base_dir": ...}
            }
        },
    )
    ```

    You should instead use the built-in IO manager `fs_io_manager`, which can be attached to your
    pipeline as a resource:

    ```python
    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={"io_manager": fs_io_manager}
            )
        ],
    )
    def my_pipeline():
        ...

    execute_pipeline(
        my_pipeline,
        run_config={
            "resources": {
                "io_manager": {"config": {"base_dir": ...}}
            }
        },
    )
    ```

    There are corresponding IO managers for other intermediate storages, such as the S3- and
    ADLS2-based storages

* We have deprecated `IntermediateStorageDefinition` and `@intermediate_storage`.

  If you have written custom intermediate storage, you should migrate to custom IO managers
  defined using the `@io_manager` API. We have provided a helper method,
  `io_manager_from_intermediate_storage`, to help migrate your existing custom intermediate
  storages to IO managers.


    ```python
    my_io_manager_def = io_manager_from_intermediate_storage(
        my_intermediate_storage_def
    )

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    "io_manager": my_io_manager_def
                }
            ),
        ],
    )
    def my_pipeline():
        ...
    ```

* We have deprecated the `intermediate_storage_defs` argument to `ModeDefinition`, in favor of the
  new IO managers, which should be attached using the `resource_defs` argument.

## Removal: `input_hydration_config` and `output_materialization_config`

Use `dagster_type_loader` instead of `input_hydration_config` and `dagster_type_materializer`
instead of `output_materialization_config`.

On `DagsterType` and type constructors in `dagster_pandas` use the `loader` argument instead of
`input_hydration_config` and the `materializer` argument instead of `dagster_type_materializer`
argument.

## Removal: `repository` key in workspace YAML

We have removed the ability to specify a repository in your workspace using the `repository:` key.
Use `load_from:` instead when specifying how to load the repositories in your workspace.

## Deprecated: `python_environment` key in workspace YAML

The `python_environment:` key is now deprecated and will be removed in a future release.

Previously, when you wanted to load a repository location in your workspace using a different
Python environment from Dagit’s Python environment, you needed to use a `python_environment:` key
under `load_from:` instead of the `python_file:` or `python_package:` keys. Now, you can simply
customize the `executable_path` in your workspace entries without needing to change to the
`python_environment:` key.

For example, the following workspace entry:

```yaml
  - python_environment:
      executable_path: "/path/to/venvs/dagster-dev-3.7.6/bin/python"
      target:
        python_package:
          package_name: dagster_examples
          location_name: dagster_examples
```

should now be expressed as:

```yaml
  - python_package:
      executable_path: "/path/to/venvs/dagster-dev-3.7.6/bin/python"
      package_name: dagster_examples
      location_name: dagster_examples
```


See our [Workspaces Overview](https://docs.dagster.io/overview/repositories-workspaces/workspaces#loading-from-an-external-environment)
for more information and examples.

## Removal: `config_field` property on definition classes

We have removed the property `config_field` on definition classes. Use `config_schema` instead.

## Removal: System Storage

We have removed the system storage abstractions, i.e. `SystemStorageDefinition` and
`@system_storage` ([deprecated in 0.9.0](#deprecation-system_storage_defs)).

Please note that the intermediate storage abstraction is also deprecated and will be removed in
0.11.0. [Use IO managers instead](#deprecation-intermediate-storage).

* We have removed the `system_storage_defs` argument (deprecated in 0.9.0) to `ModeDefinition`, in
  favor of `intermediate_storage_defs.`
* We have removed the built-in system storages, e.g. `default_system_storage_defs`
  (deprecated in 0.9.0).


## Removal: `step_keys_to_execute`

We have removed the `step_keys_to_execute` argument to `reexecute_pipeline` and
`reexecute_pipeline_iterator`, in favor of `step_selection`. This argument accepts the Dagster
selection syntax, so, for example, `*solid_a+` represents `solid_a`, all of its upstream steps,
and its immediate downstream steps.

## Breaking Change: `date_partition_range`

Starting in 0.10.0, Dagster uses the [pendulum](https://pypi.org/project/pendulum/) library to
ensure that schedules and partitions behave correctly with respect to timezones. As part of this
change, the `delta` parameter to `date_partition_range` (which determined the time different between
partitions and was a `datetime.timedelta`) has been replaced by a `delta_range` parameter
(which must be a string that's a valid argument to the `pendulum.period` function, such as
`"days"`, `"hours"`, or `"months"`).

For example, the following partition range for a monthly partition set:

```python
date_partition_range(
    start=datetime.datetime(2018, 1, 1),
    end=datetime.datetime(2019, 1, 1),
    delta=datetime.timedelta(months=1)
)
```

should now be expressed as:

```python
date_partition_range(
    start=datetime.datetime(2018, 1, 1),
    end=datetime.datetime(2019, 1, 1),
    delta_range="months"
)
```

## Breaking Change: `PartitionSetDefinition.create_schedule_definition`

When you create a schedule from a partition set using
`PartitionSetDefinition.create_schedule_definition`, you now must supply a `partition_selector`
argument that tells the scheduler which partition to use for a given schedule time.

We have added two helper functions, `create_offset_partition_selector` and
`identity_partition_selector`, that capture two common partition selectors (schedules that execute
at a fixed offset from the partition times, e.g. a schedule that creates the previous day's
partition each morning, and schedules that execute at the same time as the partition times).

The previous default partition selector was `last_partition`, which didn't always work as expected
when using the default scheduler and has been removed in favor of the two helper partition selectors
above.

For example, a schedule created from a daily partition set that fills in each partition the next
day at 10AM would be created as follows:

```python
partition_set = PartitionSetDefinition(
    name='hello_world_partition_set',
    pipeline_name='hello_world_pipeline',
    partition_fn= date_partition_range(
        start=datetime.datetime(2021, 1, 1),
        delta_range="days",
        timezone="US/Central",
    )
    run_config_fn_for_partition=my_run_config_fn,
)

schedule_definition = partition_set.create_schedule_definition(
    "daily_10am_schedule",
    "0 10 * * *",
    partition_selector=create_offset_partition_selector(lambda d: d.subtract(hours=10, days=1))
    execution_timezone="US/Central",
)
```

## Renamed: Helm values

Following convention in the [Helm docs](https://helm.sh/docs/chart_best_practices/values/#naming-conventions),
we now camel case all of our Helm values. To migrate to 0.10.0, you'll need to update your
`values.yaml` with the following renames:

* `pipeline_run` → `pipelineRun`
* `dagster_home` → `dagsterHome`
* `env_secrets` → `envSecrets`
* `env_config_maps` → `envConfigMaps`

## Restructured: `scheduler` in Helm values

When specifying the Dagster instance scheduler, rather than using a boolean field to switch between
the current options of `K8sScheduler` and `DagsterDaemonScheduler`, we now require the scheduler
type to be explicitly defined under `scheduler.type`. If the user specified `scheduler.type` has
required config, additional fields will need to be specified under `scheduler.config`.

`scheduler.type` and corresponding `scheduler.config` values are enforced via
[JSON Schema](https://helm.sh/docs/topics/charts/#schema-files).

For example, if your Helm values previously were set like this to enable the
`DagsterDaemonScheduler`:
​
```yaml
scheduler:
  k8sEnabled: false
```
​
You should instead have:
​
```yaml
scheduler:
  type: DagsterDaemonScheduler
```

## Restructured: `celery` and `k8sRunLauncher` in Helm values

`celery` and `k8sRunLauncher` now live under `runLauncher.config.celeryK8sRunLauncher` and
`runLauncher.config.k8sRunLauncher` respectively. Now, to enable celery, `runLauncher.type` must
equal `CeleryK8sRunLauncher`. To enable the vanilla K8s run launcher, `runLauncher.type` must
equal `K8sRunLauncher`.

`runLauncher.type` and corresponding `runLauncher.config` values are enforced via
[JSON Schema](https://helm.sh/docs/topics/charts/#schema-files).

For example, if your Helm values previously were set like this to enable the `K8sRunLauncher`:
​
```yaml
celery:
  enabled: false
​
k8sRunLauncher:
  enabled: true
  jobNamespace: ~
  loadInclusterConfig: true
  kubeconfigFile: ~
  envConfigMaps: []
  envSecrets: []
```
​
You should instead have:
​
```yaml
runLauncher:
  type: K8sRunLauncher
  config:
    k8sRunLauncher:
      jobNamespace: ~
      loadInclusterConfig: true
      kubeconfigFile: ~
      envConfigMaps: []
      envSecrets: []
```

## New Helm defaults

By default, `userDeployments` is enabled and the `runLauncher` is set to the `K8sRunLauncher`.
Along with the latter change, all message brokers (e.g. `rabbitmq` and `redis`) are now disabled
by default.

If you were using the `CeleryK8sRunLauncher`, one of `rabbitmq` or `redis` must now be explicitly
enabled in your Helm values.


# Migrating to 0.9.0

## Removal: `config` argument

We have removed the `config` argument to the `ConfigMapping`, `@composite_solid`, `@solid`,
`SolidDefinition`, `@executor`, `ExecutorDefinition`, `@logger`, `LoggerDefinition`, `@resource`,
and `ResourceDefinition` APIs, which we deprecated in 0.8.0, in favor of `config_schema`, as
described [here](#renaming-config).

# Migrating to 0.8.8

## Deprecation: `Materialization`

We deprecated the `Materialization` event type in favor of the new `AssetMaterialization` event type,
which requires the `asset_key` parameter. Solids yielding `Materialization` events will continue
to work as before, though the `Materialization` event will be removed in a future release.

## Deprecation: `system_storage_defs`

We are starting to deprecate "system storages" - instead of pipelines having a system storage
definition which creates an intermediate storage, pipelines now directly have an intermediate
storage definition.

- We have added an `intermediate_storage_defs` argument to `ModeDefinition`, which accepts a
  list of `IntermediateStorageDefinition`s, e.g. `s3_plus_default_intermediate_storage_defs`.
  As before, the default includes an in-memory intermediate and a local filesystem intermediate
  storage.
- We have deprecated `system_storage_defs` argument to `ModeDefinition` in favor of
  `intermediate_storage_defs`. `system_storage_defs` will be removed in 0.10.0 at the earliest.
- We have added an `@intermediate_storage` decorator, which makes it easy to define intermediate
  storages.
- We have added `s3_file_manager` and `local_file_manager` resources to replace the file managers
  that previously lived inside system storages. The airline demo has been updated to include
  an example of how to do this:
  https://github.com/dagster-io/dagster/blob/0.8.8/examples/airline_demo/airline_demo/solids.py#L171.

For example, if your `ModeDefinition` looks like this:

```python
from dagster_aws.s3 import s3_plus_default_storage_defs

ModeDefinition(system_storage_defs=s3_plus_default_storage_defs)
```

it is recommended to make it look like this:

```python
from dagster_aws.s3 import s3_plus_default_intermediate_storage_defs

ModeDefinition(intermediate_storage_defs=s3_plus_default_intermediate_storage_defs)
```

# Migrating to 0.8.7

## Loading python modules from the working directory

Loading python modules reliant on the working directory being on the PYTHONPATH is no longer
supported. The `dagster` and `dagit` CLI commands no longer add the working directory to the
PYTHONPATH when resolving modules, which may break some imports. Explicitly installed python
packages can be specified in workspaces using the `python_package` workspace yaml config option.
The `python_module` config option is deprecated and will be removed in a future release.

# Migrating to 0.8.6

## dagster-celery

The `dagster-celery` module has been broken apart to manage dependencies more coherently. There
are now three modules: `dagster-celery`, `dagster-celery-k8s`, and `dagster-celery-docker`.

Related to above, the `dagster-celery worker start` command now takes a required `-A` parameter
which must point to the `app.py` file within the appropriate module. E.g if you are using the
`celery_k8s_job_executor` then you must use the `-A dagster_celery_k8s.app` option when using the
`celery` or `dagster-celery` cli tools. Similar for the `celery_docker_executor`:
`-A dagster_celery_docker.app` must be used.

## Deprecation: `input_hydration_config` and `output_materialization_config`

We renamed the `input_hydration_config` and `output_materialization_config` decorators to
`dagster_type_` and `dagster_type_materializer` respectively. We also renamed DagsterType's
`input_hydration_config` and `output_materialization_config` arguments to `loader` and `materializer`
respectively.

For example, if your dagster type definition looks like this:

```python
from dagster import DagsterType, input_hydration_config, output_materialization_config


@input_hydration_config(config_schema=my_config_schema)
def my_loader(_context, config):
    '''some implementation'''


@output_materialization_config(config_schema=my_config_schema)
def my_materializer(_context, config):
    '''some implementation'''


MyType = DagsterType(
    input_hydration_config=my_loader,
    output_materialization_config=my_materializer,
    type_check_fn=my_type_check,
)
```

it is recommended to make it look like this:

```python
from dagster import DagsterType, dagster_type_loader, dagster_type_materializer


@dagster_type_loader(config_schema=my_config_schema)
def my_loader(_context, config):
    '''some implementation'''


@dagster_type_materializer(config_schema=my_config_schema)
def my_materializer(_context, config):
    '''some implementation'''


MyType = DagsterType(
    loader=my_loader,
    materializer=my_materializer,
    type_check_fn=my_type_check,
)
```

# Migrating to 0.8.5

## Python 3.5

Python 3.5 is no longer under test.

## `Engine` and `ExecutorConfig` -> `Executor`

`Engine` and `ExecutorConfig` have been deleted in favor of `Executor`. Instead of the `@executor` decorator decorating a function that returns an `ExecutorConfig` it should now decorate a function that returns an `Executor`.

# Migrating to 0.8.3

## Change: `gcs_resource`

Previously, the `gcs_resource` returned a `GCSResource` wrapper which had a single `client` property that returned a `google.cloud.storage.client.Client`. Now, the `gcs_resource` returns the client directly.

To update solids that use the `gcp_resource`, change:

```
context.resources.gcs.client
```

To:

```
context.resources.gcs
```

# Migrating to 0.8.0

## Repository loading

Dagit and other tools no longer load a single repository containing user definitions such as
pipelines into the same process as the framework code. Instead, they load a "workspace" that can
contain multiple repositories sourced from a variety of different external locations (e.g., Python
modules and Python virtualenvs, with containers and source control repositories soon to come).

The repositories in a workspace are loaded into their own "user" processes distinct from the
"host" framework process. Dagit and other tools now communicate with user code over an IPC
mechanism.

As a consequence, the former `repository.yaml` and the associated `-y`/`--repository-yaml` CLI
arguments are deprecated in favor of a new `workspace.yaml` file format and associated
`-w`/`--workspace-yaml` arguments.

### Steps to migrate

You should replace your `repository.yaml` files with `workspace.yaml` files, which can define a
number of possible sources from which to load repositories.

```yaml
load_from:
  - python_module:
      module_name: dagster_examples
      attribute: define_internal_dagit_repository
  - python_module: dagster_examples.intro_tutorial.repos
  - python_file: repos.py
  - python_environment:
      executable_path: "/path/to/venvs/dagster-dev-3.7.6/bin/python"
      target:
        python_module:
          module_name: dagster_examples
          location_name: dagster_examples
          attribute: define_internal_dagit_repository
```

## Repository definition

The `@scheduler` and `@repository_partitions` decorators have been removed. In addition, users
should prefer the new `@repository` decorator to instantiating `RepositoryDefinition` directly.

One consequence of this change is that `PartitionSetDefinition` names, including those defined by
a `PartitionScheduleDefinition`, must now be unique within a single repository.

### Steps to migrate

Previously you might have defined your pipelines, schedules, partition sets, and repositories in a
python file such as the following:

```python
@pipeline
def test():
    ...

@daily_schedule(
    pipeline_name='test',
    start_date=datetime.datetime(2020, 1, 1),
)
def daily_test_schedule(_):
    return {}

test_partition_set = PartitionSetDefinition(
    name="test",
    pipeline_name="test",
    partition_fn=lambda: ["test"],
    environment_dict_fn_for_partition=lambda _: {},
)

@schedules
def define_schedules():
    return [daily_test_schedule]

@repository_partitions
def define_partitions():
    return [test_partition_set]

def define_repository():
    return RepositoryDefinition('test', pipeline_defs=[test])
```

With a `repository.yaml` such as:

```yaml
repository:
  file: repo.py
  fn: define_repository

scheduler:
  file: repo.py
  fn: define_schedules

partitions:
  file: repo.py
  fn: define_partitions
```

In 0.8.0, you'll write Python like:

```python
@pipeline
def test_pipeline():
    ...

@daily_schedule(
    pipeline_name='test',
    start_date=datetime.datetime(2020, 1, 1),
)
def daily_test_schedule(_):
    return {}

test_partition_set = PartitionSetDefinition(
    name="test",
    pipeline_name="test",
    partition_fn=lambda: ["test"],
    run_config_fn_for_partition=lambda _: {},
)

@repository
def test_repository():
    return [test_pipeline, daily_test_schedule, test_partition_set]
```

Your `workspace.yaml` will look like:

```yaml
load_from:
  - python_file: repo.py
```

If you have more than one repository defined in a single Python file, you'll want to instead load
the repository using `workspace.yaml` like:

```yaml
load_from:
  - python_file:
      relative_path: repo.py
      attribute: test_repository
  - python_file:
      relative_path: repo.py
      attribute: other_repository
```

Of course, the `workspace.yaml` also supports loading from a `python_module`, or with a specific
Python interpreter from a `python_environment`.

Note that the `@repository` decorator also supports more sophisticated, lazily-loaded repositories.
Consult the documentation for the decorator for more details.

## Reloadable repositories

In 0.7.x, dagster attempted to elide the difference between a pipeline that was defined in memory
and one that was loaded through machinery that used the `ExecutionTargetHandle` machinery. This
resulted in opaque and hard-to-predict errors and unpleasant workarounds, for instance:

- Pipeline execution in test using `execute_pipeline` would suddenly fail when a multiprocess
  executor was used.
- Tests of pipelines with dagstermill solids had to resort to workarounds such as

```python
    handle = handle_for_pipeline_cli_args(
        {'module_name': 'some_module.repository', 'fn_name': 'some_pipeline'}
    )
    pipeline = handle.build_pipeline_definition()
    result = execute_pipeline(pipeline, ...)
```

In 0.8.0, we've added the `reconstructable` helper to explicitly convert in-memory pipelines into
reconstructable pipelines that can be passed between processes.

```python
@pipeline(...)
def some_pipeline():
    ...

execute_pipeline(reconstructable(some_pipeline), {'execution': {'multiprocess': {}})
```

Pipelines must be defined in module scope in order for `reconstructable` to be used. Note that
pipelines defined _interactively_, e.g., in the Python REPL, cannot be passed between processes.

## Renaming environment_dict and removing RunConfig

In 0.8.0, we've renamed the common `environment_dict` parameter to many user-facing APIs to
`run_config`, and we've dropped the previous `run_config` parameter. This change affects the
`execute_pipeline_iterator` and `execute_pipeline` APIs, the `PresetDefinition` and
`ScheduleDefinition`, and the `execute_solid` test API. Similarly, the `environment_dict_fn`, `user_defined_environment_dict_fn_for_partition`, and `environment_dict_fn_for_partition` parameters
to `ScheduleDefinition`, `PartitionSetDefinition`, and `PartitionScheduleDefinition` have been
renamed to `run_config_fn`, `user_defined_run_config_fn_for_partition`, and
`run_config_fn_for_partition` respectively.

The previous `run_config` parameter has been removed, as has the backing `RunConfig` class. This
change affects the `execute_pipeline_iterator` and `execute_pipeline` APIs, and the
`execute_solids_within_pipeline` and `execute_solid_within_pipeline` test APIs. Instead, you should
set the `mode`, `preset`, `tags`, `solid_selection`, and, in test, `raise_on_error parameters
directly.

This change is intended to reduce ambiguity around the notion of a pipeline execution's
"environment", since the config value passed as `run_config` is scoped to a single execution.

## Deprecation: `config` argument

In 0.8.0, we've renamed the common `config` parameter to the user-facing definition APIs to
`config_schema`. This is intended to reduce ambiguity between config values (provided at
execution time) and their user-specified schemas (provided at definition time). This change affects
the `ConfigMapping`, `@composite_solid`, `@solid`, `SolidDefinition`, `@executor`,
`ExecutorDefinition`, `@logger`, `LoggerDefinition`, `@resource`, and `ResourceDefinition` APIs.
In the CLI, `dagster pipeline execute` and `dagster pipeline launch` now take `-c/--config` instead
of `-e/--env`.

## Renaming solid_subset and enabling support for solid selection DSL in Python API

In 0.8.0, we've renamed the `solid_subset`/`--solid-subset` argument to
`solid_selection`/`--solid-selection` throughout the Python API and CLI. This affects the
`dagster pipeline execute`, `dagster pipeline launch`, and `dagster pipeline backfill` CLI commands,
and the `@schedule`, `@monthly_schedule`, `@weekly_schedule`, `@daily_schedule`, `@hourly_schedule`,
`ScheduleDefinition`, `PresetDefinition`, `PartitionSetDefinition`, `PartitionScheduleDefinition`,
`execute_pipeline`, `execute_pipeline_iterator`, `DagsterInstance.create_run_for_pipeline`,
`DagsterInstance.create_run` APIs.

In addition to the names of individual solids, the new `solid_selection` argument supports selection
queries like `*solid_name++` (i.e., `solid_name`, all of its ancestors, its immediate descendants,
and their immediate descendants), previously supported only in Dagit views.

## Removal of deprectated properties, methods, and arguments

- The deprecated `runtime_type` property on `InputDefinition` and `OutputDefinition` has been
  removed. Use `dagster_type` instead.
- The deprecated `has_runtime_type`, `runtime_type_named`, and `all_runtime_types` methods on
  `PipelineDefinition` have been removed. Use `has_dagster_type`, `dagster_type_named`, and
  `all_dagster_types` instead.
- The deprecated `all_runtime_types` method on `SolidDefinition` and `CompositeSolidDefinition`
  has been removed. Use `all_dagster_types` instead.
- The deprecated `metadata` argument to `SolidDefinition` and `@solid` has been removed. Use
  `tags` instead.
- The use of `is_optional` throughout the codebase was deprecated in 0.7.x and has been removed. Use
  `is_required` instead.

## Removal of Path config type

The built-in config type `Path` has been removed. Use `String`.

## dagster-bash

This package has been renamed to dagster-shell. The`bash_command_solid` and `bash_script_solid`
solid factory functions have been renamed to `create_shell_command_solid` and
`create_shell_script_solid`.

## Dask config

The config schema for the `dagster_dask.dask_executor` has changed. The previous config should
now be nested under the key `local`.

## Spark solids

`dagster_spark.SparkSolidDefinition` has been removed - use `create_spark_solid` instead.

# Migrating to 0.7.0

The 0.7.0 release contains a number of breaking API changes. While listed
in the changelog, this document goes into more detail about how to
resolve the change easily. Most of the eliminated or changed APIs
can be adjusted to with relatively straightforward changes.

The easiest way to use this guide is to search for associated
error text.

## Dagster Types

There have been substantial changes to the core dagster type APIs.

Error:

`ImportError: cannot import name 'dagster_type' from 'dagster'`

Fix:

Use `usable_as_dagster_type` instead. If dynamically generating
types, construct using `DagsterType` instead.

Error:

`ImportError: cannot import name 'as_dagster_type' from 'dagster'`

Fix:

Use `make_python_type_usable_as_dagster_type` instead.

Error:

`dagster.core.errors.DagsterInvalidDefinitionError: type_check_fn argument type "BadType" must take 2 arguments, received 1`

Fix:

Add a context argument (named `_`, `_context`, `context`, or `context_`) as the first argument
of the `type_check_fn`. The second argument is the value being type-checked.

Further Information:

We have eliminated the `@dagster_type` and `as_dagster_type`
APIs, which previously were promoted as our primary type
creation API. This API automatically created a mapping
between a Python type and a Dagster Type. While convenient,
this ended up causing unpredictable behavior based on import
order, as well as being wholly incompatible with dynamically
created Dagster types.

Our core type creation API is now the `DagsterType` class. It creates a
Dagster type (which is just an instance of `DagsterType`) that can be passed
to `InputDefinition` and `OutputDefinition`.

The functionality of `@dagster_type` is preserved, but under a different name:
`usable_as_dagster_type`. This decorator signifies that the author wants
a bare Python type to be usable in contexts that expect dagster types, such as
an `InputDefinition` or `OutputDefinition`.

Any user that had been programatically creating dagster types and was forced
to decorate classes in local scope using `@dagster_type` and return that class
should instead just create a `DagsterType` directly.

`as_dagster_type` has replaced by `make_python_type_usable_as_dagster_type`.
The semantics of `as_dagster_type` did not indicate what is was actually doing
very well. This function is meant to take an _existing_ type -- often from
a library that one doesn't control -- and make that type usable as a dagster
type, the second argument.

The `type_check_fn` argument has been renamed from `type_check` and now takes
two arguments instead of one. The first argument is a instance of `TypeCheckContext`;
the second argument is the value being checked. This allows the type check
to have access to resources.

## Config System

The config APIs have been renamed to have no collisions with names in neither python's
`typing` API nor the dagster type system. Here are some example errors:

Error:

`dagster.core.errors.DagsterInvariantViolationError: Cannot resolve Dagster Type Optional.Int to a config type. Repr of type: <dagster.core.types.dagster_type.OptionalType object at 0x102bb2a50>`

Fix:

Use `Noneable` of `Optional`.

Error:

`TypeError: 'DagsterDictApi' object is not callable`

Fix:

Pass a raw python dictionary instead of Dict.

`config=Dict({'foo': str})` becomes `config={'foo': str}`

Error:

`ImportError: cannot import name 'PermissiveDict' from 'dagster'`

Fix:

Use `Permissive` instead.

Error:

`dagster.core.errors.DagsterInvariantViolationError: Cannot use List in the context of config. Please use a python list (e.g. [int]) or dagster.Array (e.g. Array(int)) instead.`

Fix:

This happens when a properly constructed List is used within config. Use Array instead.

Error:

`dagster.core.errors.DagsterInvalidDefinitionError: Invalid type: dagster_type must be DagsterType, a python scalar, or a python type that has been marked usable as a dagster type via @usable_dagster_type or make_python_type_usable_as_dagster_type: got <dagster.config.config_type.Noneable object at 0x1029c8a10>.`

Fix:

This happens when a List takes an invalid argument and is never constructed.
The error could be much better. This is what happens a config type (in this
case `Noneable`) is passed to a `List`. The fix is to use either `Array` or
to use a bare list with a single element, which is a config type.

## Required Resources

Any solid, type, or configuration function that accesses a resource off of a context
object must declare that resource key with a `required_resource_key` argument.

Error:

`DagsterUnknownResourceError: Unknown resource <resource_name>. Specify <resource_name> as a required resource on the compute / config function that accessed it.`

Fix:

Find any references to `context.resources.<resource_name>`, and ensure that the enclosing
solid definition, type definition, or config function has the resource key specified
in its `required_resource_key` argument.

Further information:

When only a subset of solids are being executed in a given process, we only need to
initialize resources that will be used by that subset of solids. In order to improve
the performance of pipeline execution, we need each solid and type to explicitly declare
its required resources.

As a result, we should see improved performance for pipeline subset execution,
multiprocess execution, and retry execution.

## RunConfig Removed

Error:

`AttributeError: 'ComputeExecutionContext' object has no attribute 'run_config'`

Fix:

Replace all references to `context.run_config` with `context.pipeline_run`. The `run_config` field
on the pipeline execution context has been removed and replaced with `pipeline_run`, a `PipelineRun`
instance. Along with the fields previously on `RunConfig`, this also includes the pipeline run
status.

## Scheduler

Scheduler configuration has been moved to the `dagster.yaml`. After upgrading, the previous schedule
history is no longer compatible with the new storage.

Make sure you delete your existing `$DAGSTER_HOME/schedules` directory, then run:

```
dagster schedule wipe && dagster schedule up
```

Error:

`TypeError: schedules() got an unexpected keyword argument 'scheduler'`

Fix:

The `@schedules` decorator no longer takes a `scheduler` argument. Remove the argument and instead
configure the scheduler on the instance.

Instead of:

```
@schedules(scheduler=SystemCronScheduler)
def define_schedules():
    ...
```

Remove the `scheduler` argument:

```
@schedules
def define_schedules():
    ...
```

Configure the scheduler on your instance by adding the following to `$DAGSTER_HOME/dagster.yaml`:

```
scheduler:
    module: dagster_cron.cron_scheduler
    class: SystemCronScheduler
```

Error:

`TypeError: <lambda>() takes 0 positional arguments but 1 was given"`

Stack Trace:

```
    File ".../dagster/python_modules/dagster/dagster/core/definitions/schedule.py", line 171, in should_execute
        return self._should_execute(context)
```

Fix:

The `should_execute` and `environment_dict_fn` argument to `ScheduleDefinition` now has a required
first argument `context`, representing the `ScheduleExecutionContext`.

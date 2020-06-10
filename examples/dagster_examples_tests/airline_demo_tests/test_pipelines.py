import os

# pylint: disable=unused-argument
import pytest

from dagster import execute_pipeline, file_relative_path
from dagster.core.definitions.reconstructable import ReconstructablePipeline
from dagster.core.instance import DagsterInstance
from dagster.utils import load_yaml_from_globs

ingest_pipeline = ReconstructablePipeline.for_module(
    'dagster_examples.airline_demo.pipelines', 'define_airline_demo_ingest_pipeline',
)

warehouse_pipeline = ReconstructablePipeline.for_module(
    'dagster_examples.airline_demo.pipelines', 'define_airline_demo_warehouse_pipeline',
)


def config_path(relative_path):
    return file_relative_path(
        __file__, os.path.join('../../dagster_examples/airline_demo/environments/', relative_path)
    )


@pytest.mark.db
@pytest.mark.nettest
@pytest.mark.py3
@pytest.mark.spark
def test_ingest_pipeline_fast(postgres, pg_hostname):
    ingest_config_dict = load_yaml_from_globs(
        config_path('test_base.yaml'), config_path('local_fast_ingest.yaml')
    )
    result_ingest = execute_pipeline(
        pipeline=ingest_pipeline,
        mode='local',
        run_config=ingest_config_dict,
        instance=DagsterInstance.local_temp(),
    )

    assert result_ingest.success


@pytest.mark.db
@pytest.mark.nettest
@pytest.mark.py3
@pytest.mark.spark
def test_ingest_pipeline_fast_filesystem_storage(postgres, pg_hostname):
    ingest_config_dict = load_yaml_from_globs(
        config_path('test_base.yaml'),
        config_path('local_fast_ingest.yaml'),
        config_path('filesystem_storage.yaml'),
    )
    result_ingest = execute_pipeline(
        pipeline=ingest_pipeline,
        mode='local',
        run_config=ingest_config_dict,
        instance=DagsterInstance.local_temp(),
    )

    assert result_ingest.success


@pytest.mark.db
@pytest.mark.nettest
@pytest.mark.py3
@pytest.mark.spark
@pytest.mark.skipif('"win" in sys.platform', reason="avoiding the geopandas tests")
def test_airline_pipeline_1_warehouse(postgres, pg_hostname):
    warehouse_config_object = load_yaml_from_globs(
        config_path('test_base.yaml'), config_path('local_warehouse.yaml')
    )
    result_warehouse = execute_pipeline(
        pipeline=warehouse_pipeline,
        mode='local',
        run_config=warehouse_config_object,
        instance=DagsterInstance.local_temp(),
    )
    assert result_warehouse.success


####################################################################################################
# These tests are provided to help distinguish issues using the S3 object store from issues using
# Airflow, but add too much overhead (~30m) to run on each push
@pytest.mark.skip
def test_airline_pipeline_s3_0_ingest(postgres, pg_hostname):
    ingest_config_dict = load_yaml_from_globs(
        config_path('test_base.yaml'),
        config_path('s3_storage.yaml'),
        config_path('local_fast_ingest.yaml'),
    )

    result_ingest = execute_pipeline(
        ingest_pipeline, ingest_config_dict, instance=DagsterInstance.local_temp()
    )

    assert result_ingest.success


@pytest.mark.skip
def test_airline_pipeline_s3_1_warehouse(postgres, pg_hostname):
    warehouse_config_object = load_yaml_from_globs(
        config_path('test_base.yaml'),
        config_path('s3_storage.yaml'),
        config_path('local_warehouse.yaml'),
    )

    result_warehouse = execute_pipeline(
        warehouse_pipeline, warehouse_config_object, instance=DagsterInstance.local_temp()
    )
    assert result_warehouse.success


####################################################################################################

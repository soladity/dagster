def define_demo_repo():
    # Lazy import here to prevent deps issues

    from dagster import RepositoryDefinition
    from dagster_examples.toys.error_monster import error_monster
    from dagster_examples.toys.sleepy import sleepy_pipeline
    from dagster_examples.toys.log_spew import log_spew
    from dagster_examples.toys.many_events import many_events
    from dagster_examples.toys.composition import composition
    from dagster_examples.toys.pandas_hello_world import (
        pandas_hello_world_pipeline,
        pandas_hello_world_pipeline_no_config,
    )
    from dagster_examples.airline_demo.pipelines import (
        airline_demo_ingest_pipeline,
        airline_demo_warehouse_pipeline,
    )
    from dagster_examples.event_pipeline_demo.pipelines import event_ingest_pipeline
    from dagster_examples.pyspark_pagerank.pyspark_pagerank_pipeline import pyspark_pagerank
    from dagster_pandas.examples import papermill_pandas_hello_world_pipeline

    return RepositoryDefinition(
        name='demo_repository',
        pipeline_defs=[
            pandas_hello_world_pipeline_no_config,
            pandas_hello_world_pipeline,
            sleepy_pipeline,
            error_monster,
            log_spew,
            many_events,
            composition,
            airline_demo_ingest_pipeline,
            airline_demo_warehouse_pipeline,
            event_ingest_pipeline,
            pyspark_pagerank,
            papermill_pandas_hello_world_pipeline,
        ],
    )

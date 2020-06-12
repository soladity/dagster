from dagster import DagsterInstance, execute_pipeline, lambda_solid, pipeline, reconstructable


def define_pipeline():
    @lambda_solid
    def ping():
        return 'ping'

    @pipeline
    def simple():
        ping()

    return simple


def test_multiproc_markers():
    instance = DagsterInstance.local_temp()
    result = execute_pipeline(
        reconstructable(define_pipeline),
        instance=instance,
        run_config={'execution': {'multiprocess': {}}, 'storage': {'filesystem': {}}},
    )
    assert result.success
    events = instance.all_logs(result.run_id)
    start_markers = {}
    end_markers = {}
    for event in events:
        dagster_event = event.dagster_event
        if dagster_event.is_engine_event:
            if dagster_event.engine_event_data.marker_start:
                key = '{step}.{marker}'.format(
                    step=event.step_key, marker=dagster_event.engine_event_data.marker_start
                )
                start_markers[key] = event.timestamp
            if dagster_event.engine_event_data.marker_end:
                key = '{step}.{marker}'.format(
                    step=event.step_key, marker=dagster_event.engine_event_data.marker_end
                )
                end_markers[key] = event.timestamp

    seen = set()
    assert set(start_markers.keys()) == set(end_markers.keys())
    for key in end_markers:
        assert end_markers[key] - start_markers[key] > 0
        seen.add(key)

    assert 'ping.compute.multiprocess_subprocess_init' in end_markers

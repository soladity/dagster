from dagster import file_relative_path, seven
from dagster.api.execute_pipeline import api_execute_pipeline
from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.events import DagsterEventType
from dagster.core.instance import DagsterInstance


def test_execute_pipeline_with_ipc():

    with seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)
        events = []
        for event in api_execute_pipeline(
            instance,
            ReconstructableRepository.from_yaml(
                file_relative_path(__file__, 'repository_file.yaml')
            ),
            'foo',
            {},
            'default',
            None,
        ):
            events.append(event)

        assert len(events) == 11
        assert events[0].event_type_value == DagsterEventType.PIPELINE_START.value
        assert events[-1].event_type_value == DagsterEventType.PIPELINE_SUCCESS.value

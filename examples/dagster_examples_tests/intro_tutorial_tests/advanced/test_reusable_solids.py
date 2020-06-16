from dagster_examples.intro_tutorial.advanced.solids.reusable_solids import split_cereals

from dagster import execute_solid


def test_split():
    res = execute_solid(
        split_cereals,
        input_values={'cereals': []},
        run_config={
            'solids': {'split_cereals': {'config': {'process_hot': False, 'process_cold': False}}}
        },
    )
    assert not res.output_events_during_compute

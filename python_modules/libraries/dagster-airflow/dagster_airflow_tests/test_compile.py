from dagster_airflow.compile import coalesce_execution_steps
from dagster_examples.toys.composition import composition

from dagster.core.definitions.executable import InMemoryExecutablePipeline
from dagster.core.execution.plan.plan import ExecutionPlan
from dagster.core.system_config.objects import EnvironmentConfig


def test_compile():
    # TODO: remove dependency on legacy_examples
    # https://github.com/dagster-io/dagster/issues/2653
    environment_config = EnvironmentConfig.build(
        composition, {'solids': {'add_four': {'inputs': {'num': {'value': 1}}}}},
    )

    plan = ExecutionPlan.build(InMemoryExecutablePipeline(composition), environment_config)

    res = coalesce_execution_steps(plan)

    assert set(res.keys()) == {
        'add_four.add_two.add_one',
        'add_four.add_two.add_one_2',
        'add_four.add_two_2.add_one',
        'add_four.add_two_2.add_one_2',
        'div_four.div_two',
        'div_four.div_two_2',
        'int_to_float',
    }

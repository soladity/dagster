import pytest
from dagster import Failure, graph
from docs_snippets_crag.concepts.solids_pipelines.op_events import (
    my_asset_op,
    my_failure_metadata_op,
    my_failure_op,
    my_metadata_expectation_op,
    my_metadata_output,
    my_named_yield_op,
    my_retry_op,
    my_simple_return_op,
    my_simple_yield_op,
)


def execute_op_in_graph(an_op, **kwargs):
    @graph
    def my_graph():
        if kwargs:
            return an_op(**kwargs)
        else:
            return an_op()

    result = my_graph.execute_in_process()
    return result


def generate_stub_input_values(op):
    input_values = {}

    default_values = {"String": "abc", "Int": 1, "Any": []}

    input_defs = op.input_defs
    for input_def in input_defs:
        input_values[input_def.name] = default_values[str(input_def.dagster_type.display_name)]

    return input_values


def test_ops_compile_and_execute():
    ops = [
        my_simple_yield_op,
        my_simple_return_op,
        my_named_yield_op,
        my_metadata_output,
        my_metadata_expectation_op,
        my_retry_op,
        my_asset_op,
    ]

    for op in ops:
        input_values = generate_stub_input_values(op)
        result = execute_op_in_graph(op, **input_values)
        assert result
        assert result.success


def test_failure_op():
    with pytest.raises(Failure):
        execute_op_in_graph(my_failure_op)


def test_failure_metadata_op():
    with pytest.raises(Failure):
        execute_op_in_graph(my_failure_metadata_op)

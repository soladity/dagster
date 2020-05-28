import re

import pytest

from dagster import DagsterInvariantViolationError, execute_pipeline, execute_pipeline_iterator
from dagster.core.test_utils import step_output_event_filter

from .test_subset_selector import foo_pipeline


def test_execute_pipeline_with_solid_subset_single_clause():
    pipeline_result_full = execute_pipeline(foo_pipeline)
    assert pipeline_result_full.success
    assert pipeline_result_full.result_for_solid('add_one').output_value() == 7
    assert len(pipeline_result_full.solid_result_list) == 5

    pipeline_result_up = execute_pipeline(foo_pipeline, solid_subset=['*add_nums'])
    assert pipeline_result_up.success
    assert pipeline_result_up.result_for_solid('add_nums').output_value() == 3
    assert len(pipeline_result_up.solid_result_list) == 3

    pipeline_result_down = execute_pipeline(
        foo_pipeline,
        environment_dict={
            'solids': {'add_nums': {'inputs': {'num1': {'value': 1}, 'num2': {'value': 2}}}}
        },
        solid_subset=['add_nums++'],
    )
    assert pipeline_result_down.success
    assert pipeline_result_down.result_for_solid('add_one').output_value() == 7
    assert len(pipeline_result_down.solid_result_list) == 3


def test_execute_pipeline_with_solid_subset_multi_clauses():
    result_multi_disjoint = execute_pipeline(
        foo_pipeline, solid_subset=['return_one', 'return_two', 'add_nums+']
    )
    assert result_multi_disjoint.success
    assert result_multi_disjoint.result_for_solid('multiply_two').output_value() == 6
    assert len(result_multi_disjoint.solid_result_list) == 4

    result_multi_overlap = execute_pipeline(
        foo_pipeline, solid_subset=['return_one++', 'add_nums+', 'return_two']
    )
    assert result_multi_overlap.success
    assert result_multi_overlap.result_for_solid('multiply_two').output_value() == 6
    assert len(result_multi_overlap.solid_result_list) == 4

    result_multi_with_invalid = execute_pipeline(foo_pipeline, solid_subset=['a', '*add_nums'])
    assert result_multi_with_invalid.success
    assert result_multi_with_invalid.result_for_solid('add_nums').output_value() == 3
    assert len(result_multi_with_invalid.solid_result_list) == 3


def test_execute_pipeline_with_solid_subset_invalid():
    invalid_input = ['return_one,return_two']

    with pytest.raises(
        DagsterInvariantViolationError,
        match=re.escape(
            'No qualified solid subset found for solid_subset={input}'.format(input=invalid_input)
        ),
    ):
        execute_pipeline(foo_pipeline, solid_subset=invalid_input)


def test_execute_pipeline_iterator_with_solid_subset_query():

    output_event_iterator = step_output_event_filter(execute_pipeline_iterator(foo_pipeline))
    events = list(output_event_iterator)
    assert len(events) == 5

    iterator_up = step_output_event_filter(
        execute_pipeline_iterator(foo_pipeline, solid_subset=['*add_nums'])
    )
    events_up = list(iterator_up)
    assert len(events_up) == 3

    iterator_down = step_output_event_filter(
        execute_pipeline_iterator(
            foo_pipeline,
            environment_dict={
                'solids': {'add_nums': {'inputs': {'num1': {'value': 1}, 'num2': {'value': 2}}}}
            },
            solid_subset=['add_nums++'],
        )
    )
    events_down = list(iterator_down)
    assert len(events_down) == 3

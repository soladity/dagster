# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_basic_input_output_expectations 1'] = [
    {
        '__typename': 'StepExpectationResultEvent',
        'expectationResult': {
            'message': None,
            'name': None,
            'resultMetadataJsonString': None,
            'success': True
        },
        'level': 'INFO',
        'message': 'DagsterEventType.STEP_EXPECTATION_RESULT for step df_expectations_solid.output.sum_df.expectation.some_expectation',
        'step': {
            'key': 'df_expectations_solid.output.sum_df.expectation.some_expectation',
            'solidHandleID': 'df_expectations_solid'
        }
    },
    {
        '__typename': 'StepExpectationResultEvent',
        'expectationResult': {
            'message': None,
            'name': None,
            'resultMetadataJsonString': None,
            'success': True
        },
        'level': 'INFO',
        'message': 'DagsterEventType.STEP_EXPECTATION_RESULT for step df_expectations_solid.output.result.expectation.other_expectation',
        'step': {
            'key': 'df_expectations_solid.output.result.expectation.other_expectation',
            'solidHandleID': 'df_expectations_solid'
        }
    }
]

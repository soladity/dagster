# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_required_resources 1'] = {
    'pipeline': {
        'name': 'required_resource_pipeline',
        'solids': [
            {
                'definition': {
                    'requiredResources': [
                        {
                            'resourceKey': 'R1'
                        }
                    ]
                }
            }
        ]
    }
}

snapshots['test_mode_fetch_resources 1'] = {
    'pipeline': {
        '__typename': 'Pipeline',
        'modes': [
            {
                'name': 'add_mode',
                'resources': [
                    {
                        'configField': {
                            'configType': {
                                'name': 'Int'
                            }
                        },
                        'description': None,
                        'name': 'op'
                    }
                ]
            },
            {
                'name': 'double_adder',
                'resources': [
                    {
                        'configField': {
                            'configType': {
                                'fields': [
                                    {
                                        'configType': {
                                            'name': 'Int'
                                        },
                                        'name': 'num_one'
                                    },
                                    {
                                        'configType': {
                                            'name': 'Int'
                                        },
                                        'name': 'num_two'
                                    }
                                ],
                                'name': None
                            }
                        },
                        'description': None,
                        'name': 'op'
                    }
                ]
            },
            {
                'name': 'mult_mode',
                'resources': [
                    {
                        'configField': {
                            'configType': {
                                'name': 'Int'
                            }
                        },
                        'description': None,
                        'name': 'op'
                    }
                ]
            }
        ]
    }
}

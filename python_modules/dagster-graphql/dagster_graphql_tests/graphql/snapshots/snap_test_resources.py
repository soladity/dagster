# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_mode_fetch_resources 1'] = {
    'pipelineOrError': {
        '__typename': 'Pipeline',
        'modes': [
            {
                'name': 'add_mode',
                'resources': [
                    {
                        'configField': None,
                        'description': None,
                        'name': 'asset_store'
                    },
                    {
                        'configField': {
                            'configType': {
                                'key': 'Int'
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
                        'configField': None,
                        'description': None,
                        'name': 'asset_store'
                    },
                    {
                        'configField': {
                            'configType': {
                                'fields': [
                                    {
                                        'configType': {
                                            'key': 'Int'
                                        },
                                        'name': 'num_one'
                                    },
                                    {
                                        'configType': {
                                            'key': 'Int'
                                        },
                                        'name': 'num_two'
                                    }
                                ],
                                'key': 'Shape.fc3adbbf54d7ee8b03e7f0116e13d34e253c5bcf'
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
                        'configField': None,
                        'description': None,
                        'name': 'asset_store'
                    },
                    {
                        'configField': {
                            'configType': {
                                'key': 'Int'
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

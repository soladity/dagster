# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['TestAssetAwareEventLog.test_all_asset_keys[asset_aware_instance_in_process_env] 1'] = {
    'assetsOrError': {
        '__typename': 'AssetConnection',
        'nodes': [
            {
                'key': {
                    'path': [
                        'a'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'b'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'c'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'dummy_foreign_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'first_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'hanging_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'never_runs_asset'
                    ]
                }
            }
        ]
    }
}

snapshots['TestAssetAwareEventLog.test_all_asset_keys[postgres_with_default_run_launcher_managed_grpc_env] 1'] = {
    'assetsOrError': {
        '__typename': 'AssetConnection',
        'nodes': [
            {
                'key': {
                    'path': [
                        'a'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'b'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'c'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'dummy_foreign_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'first_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'hanging_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'never_runs_asset'
                    ]
                }
            }
        ]
    }
}

snapshots['TestAssetAwareEventLog.test_all_asset_keys[sqlite_with_default_run_launcher_managed_grpc_env] 1'] = {
    'assetsOrError': {
        '__typename': 'AssetConnection',
        'nodes': [
            {
                'key': {
                    'path': [
                        'a'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'b'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'c'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'dummy_foreign_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'first_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'hanging_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'never_runs_asset'
                    ]
                }
            }
        ]
    }
}

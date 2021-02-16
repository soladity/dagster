# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['TestAssetAwareEventLog.test_get_all_asset_keys[in_memory_instance_in_process_env] 1'] = {
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
            }
        ]
    }
}

snapshots['TestAssetAwareEventLog.test_get_all_asset_keys[sqlite_with_default_run_launcher_managed_grpc_env] 1'] = {
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
            }
        ]
    }
}

snapshots['TestAssetAwareEventLog.test_get_asset_key_materialization[in_memory_instance_in_process_env] 1'] = {
    'assetOrError': {
        'assetMaterializations': [
            {
                'materializationEvent': {
                    'materialization': {
                        'label': 'a'
                    }
                }
            }
        ]
    }
}

snapshots['TestAssetAwareEventLog.test_get_asset_key_materialization[sqlite_with_default_run_launcher_managed_grpc_env] 1'] = {
    'assetOrError': {
        '__typename': 'AssetNotFoundError'
    }
}

snapshots['TestAssetAwareEventLog.test_get_asset_key_not_found[in_memory_instance_in_process_env] 1'] = {
    'assetOrError': {
        '__typename': 'AssetNotFoundError'
    }
}

snapshots['TestAssetAwareEventLog.test_get_asset_key_not_found[sqlite_with_default_run_launcher_managed_grpc_env] 1'] = {
    'assetOrError': {
        '__typename': 'AssetNotFoundError'
    }
}

snapshots['TestAssetAwareEventLog.test_get_partitioned_asset_key_materialization[in_memory_instance_in_process_env] 1'] = {
    'assetOrError': {
        'assetMaterializations': [
            {
                'materializationEvent': {
                    'materialization': {
                        'label': 'a'
                    }
                },
                'partition': 'partition_1'
            }
        ]
    }
}

snapshots['TestAssetAwareEventLog.test_get_partitioned_asset_key_materialization[sqlite_with_default_run_launcher_managed_grpc_env] 1'] = {
    'assetOrError': {
        'assetMaterializations': [
            {
                'materializationEvent': {
                    'materialization': {
                        'label': 'a'
                    }
                },
                'partition': 'partition_1'
            }
        ]
    }
}

snapshots['TestAssetAwareEventLog.test_get_prefixed_asset_keys[in_memory_instance_in_process_env] 1'] = {
    'assetsOrError': {
        '__typename': 'AssetConnection',
        'nodes': [
            {
                'key': {
                    'path': [
                        'a'
                    ]
                }
            }
        ]
    }
}

snapshots['TestAssetAwareEventLog.test_get_prefixed_asset_keys[sqlite_with_default_run_launcher_managed_grpc_env] 1'] = {
    'assetsOrError': {
        '__typename': 'AssetConnection',
        'nodes': [
            {
                'key': {
                    'path': [
                        'a'
                    ]
                }
            }
        ]
    }
}

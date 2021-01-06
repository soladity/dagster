from dagster import check
from dagster.core.definitions.events import AssetKey
from dagster.core.events import DagsterEventType
from dagster_graphql.implementation.utils import capture_dauphin_error


@capture_dauphin_error
def get_assets(graphene_info, prefix_path):
    instance = graphene_info.context.instance
    if not instance.is_asset_aware:
        return graphene_info.schema.type_named("AssetsNotSupportedError")(
            message="The configured event log storage is not asset aware."
        )

    asset_keys = instance.all_asset_keys(prefix_path=prefix_path)
    return graphene_info.schema.type_named("AssetConnection")(
        nodes=[graphene_info.schema.type_named("Asset")(key=asset_key) for asset_key in asset_keys]
    )


def get_asset(graphene_info, asset_key):
    check.inst_param(asset_key, "asset_key", AssetKey)
    instance = graphene_info.context.instance
    if not instance.is_asset_aware:
        return graphene_info.schema.type_named("AssetsNotSupportedError")(
            message="The configured event log storage is not asset aware."
        )

    if not instance.has_asset_key(asset_key):
        return graphene_info.schema.type_named("AssetNotFoundError")(asset_key=asset_key)

    return graphene_info.schema.type_named("Asset")(key=asset_key)


def get_asset_events(graphene_info, asset_key, partitions=None, cursor=None, limit=None):
    check.inst_param(asset_key, "asset_key", AssetKey)
    check.opt_str_param(cursor, "cursor")
    check.opt_int_param(limit, "limit")
    instance = graphene_info.context.instance
    if not instance.is_asset_aware:
        return graphene_info.schema.type_named("AssetsNotSupportedError")(
            message="The configured event log storage is not asset aware."
        )
    events = instance.events_for_asset_key(asset_key, partitions, cursor, limit)
    return [
        event
        for record_id, event in events
        if event.is_dagster_event
        and event.dagster_event.event_type_value == DagsterEventType.STEP_MATERIALIZATION.value
    ]


def get_asset_run_ids(graphene_info, asset_key):
    check.inst_param(asset_key, "asset_key", AssetKey)
    instance = graphene_info.context.instance
    if not instance.is_asset_aware:
        return graphene_info.schema.type_named("AssetsNotSupportedError")(
            message="The configured event log storage is not asset aware."
        )

    return instance.run_ids_for_asset_key(asset_key)


def get_assets_for_run_id(graphene_info, run_id):
    check.str_param(run_id, "run_id")

    records = graphene_info.context.instance.all_logs(run_id)
    asset_keys = [
        record.dagster_event.asset_key
        for record in records
        if record.is_dagster_event and record.dagster_event.asset_key
    ]
    return [graphene_info.schema.type_named("Asset")(key=asset_key) for asset_key in asset_keys]

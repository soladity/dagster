from dagster_graphql import dauphin
from dagster_graphql.implementation.fetch_assets import get_asset_events, get_asset_run_ids
from dagster_graphql.implementation.fetch_runs import get_run_by_id
from dagster_graphql.schema.runs import construct_basic_params

from dagster import check
from dagster.core.events.log import EventRecord
from dagster.core.storage.pipeline_run import PipelineRunsFilter

from .errors import DauphinError


class DauphinAssetKey(dauphin.ObjectType):
    class Meta(object):
        name = 'AssetKey'

    path = dauphin.non_null_list(dauphin.String)


class DauphinAsset(dauphin.ObjectType):
    class Meta(object):
        name = 'Asset'

    key = dauphin.NonNull('AssetKey')
    assetMaterializations = dauphin.Field(
        dauphin.non_null_list('AssetMaterialization'), cursor=dauphin.String(), limit=dauphin.Int(),
    )
    runs = dauphin.Field(
        dauphin.non_null_list('PipelineRun'), cursor=dauphin.String(), limit=dauphin.Int(),
    )

    def resolve_assetMaterializations(self, graphene_info, **kwargs):
        return [
            graphene_info.schema.type_named('AssetMaterialization')(event=event)
            for event in get_asset_events(
                graphene_info, self.key, kwargs.get('cursor'), kwargs.get('limit')
            )
        ]

    def resolve_runs(self, graphene_info, **kwargs):
        cursor = kwargs.get('cursor')
        limit = kwargs.get('limit')

        run_ids = get_asset_run_ids(graphene_info, self.key)

        if not run_ids:
            return []

        # for now, handle cursor/limit here instead of in the DB layer
        if cursor:
            try:
                idx = run_ids.index(cursor)
                run_ids = run_ids[idx:]
            except ValueError:
                return []

        if limit:
            run_ids = run_ids[:limit]

        return [
            graphene_info.schema.type_named('PipelineRun')(r)
            for r in graphene_info.context.instance.get_runs(
                filters=PipelineRunsFilter(run_ids=run_ids)
            )
        ]


class DauphinAssetMaterialization(dauphin.ObjectType):
    class Meta(object):
        name = 'AssetMaterialization'

    def __init__(self, event):
        self._event = check.inst_param(event, 'event', EventRecord)

    materializationEvent = dauphin.NonNull('StepMaterializationEvent')
    runOrError = dauphin.NonNull('PipelineRunOrError')

    def resolve_materializationEvent(self, graphene_info):
        return graphene_info.schema.type_named('StepMaterializationEvent')(
            materialization=self._event.dagster_event.step_materialization_data.materialization,
            **construct_basic_params(self._event, None)
        )

    def resolve_runOrError(self, graphene_info):
        return get_run_by_id(graphene_info, self._event.run_id)


class DauphinAssetsNotSupportedError(dauphin.ObjectType):
    class Meta(object):
        name = 'AssetsNotSupportedError'
        interfaces = (DauphinError,)


class DauphinAssetsOrError(dauphin.Union):
    class Meta(object):
        name = 'AssetsOrError'
        types = ('AssetConnection', 'AssetsNotSupportedError')


class DauphinAssetConnection(dauphin.ObjectType):
    class Meta(object):
        name = 'AssetConnection'

    nodes = dauphin.non_null_list('Asset')


class DauphinAssetOrError(dauphin.Union):
    class Meta(object):
        name = 'AssetOrError'
        types = ('Asset', 'AssetsNotSupportedError')

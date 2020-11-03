from dagster import check
from dagster.config.validate import validate_config_from_snap
from dagster.core.host_representation import (
    ExternalExecutionPlan,
    ExternalPipeline,
    PipelineSelector,
    RepositorySelector,
)
from graphql.execution.base import ResolveInfo

from .utils import UserFacingGraphQLError, capture_dauphin_error


def get_full_external_pipeline_or_raise(graphene_info, selector):
    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(selector, "selector", PipelineSelector)

    if not graphene_info.context.has_external_pipeline(selector):
        raise UserFacingGraphQLError(
            graphene_info.schema.type_named("PipelineNotFoundError")(selector=selector)
        )

    return graphene_info.context.get_full_external_pipeline(selector)


def get_external_pipeline_or_raise(graphene_info, selector):
    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(selector, "selector", PipelineSelector)

    from dagster_graphql.schema.errors import DauphinInvalidSubsetError

    full_pipeline = get_full_external_pipeline_or_raise(graphene_info, selector)

    if selector.solid_selection is None:
        return full_pipeline

    for solid_name in selector.solid_selection:
        if not full_pipeline.has_solid_invocation(solid_name):
            raise UserFacingGraphQLError(
                DauphinInvalidSubsetError(
                    message='Solid "{solid_name}" does not exist in "{pipeline_name}"'.format(
                        solid_name=solid_name, pipeline_name=selector.pipeline_name
                    ),
                    pipeline=graphene_info.schema.type_named("Pipeline")(full_pipeline),
                )
            )

    return graphene_info.context.get_subset_external_pipeline(selector)


def ensure_valid_config(external_pipeline, mode, run_config):
    check.inst_param(external_pipeline, "external_pipeline", ExternalPipeline)
    check.str_param(mode, "mode")
    # do not type check run_config so that validate_config_from_snap throws

    validated_config = validate_config_from_snap(
        config_schema_snapshot=external_pipeline.config_schema_snapshot,
        config_type_key=external_pipeline.root_config_key_for_mode(mode),
        config_value=run_config,
    )

    if not validated_config.success:
        from dagster_graphql.schema.errors import DauphinPipelineConfigValidationInvalid

        raise UserFacingGraphQLError(
            DauphinPipelineConfigValidationInvalid.for_validation_errors(
                external_pipeline, validated_config.errors
            )
        )

    return validated_config


def ensure_valid_step_keys(full_external_execution_plan, step_keys):
    check.inst_param(
        full_external_execution_plan, "full_external_execution_plan", ExternalExecutionPlan
    )
    check.opt_list_param(step_keys, "step_keys", of_type=str)

    if not step_keys:
        return

    for step_key in step_keys:
        if not full_external_execution_plan.has_step(step_key):
            from dagster_graphql.schema.errors import DauphinInvalidStepError

            raise UserFacingGraphQLError(DauphinInvalidStepError(invalid_step_key=step_key))


def get_external_execution_plan_or_raise(
    graphene_info, external_pipeline, mode, run_config, step_keys_to_execute
):
    full_external_execution_plan = graphene_info.context.get_external_execution_plan(
        external_pipeline=external_pipeline,
        run_config=run_config,
        mode=mode,
        step_keys_to_execute=None,
    )

    if not step_keys_to_execute:
        return full_external_execution_plan

    ensure_valid_step_keys(full_external_execution_plan, step_keys_to_execute)

    return graphene_info.context.get_external_execution_plan(
        external_pipeline=external_pipeline,
        run_config=run_config,
        mode=mode,
        step_keys_to_execute=step_keys_to_execute,
    )


@capture_dauphin_error
def fetch_repositories(graphene_info):
    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    return graphene_info.schema.type_named("RepositoryConnection")(
        nodes=[
            graphene_info.schema.type_named("Repository")(
                repository=repository, repository_location=location
            )
            for location in graphene_info.context.repository_locations
            for repository in location.get_repositories().values()
        ]
    )


@capture_dauphin_error
def fetch_repository(graphene_info, repository_selector):
    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(repository_selector, "repository_selector", RepositorySelector)

    if graphene_info.context.has_repository_location(repository_selector.location_name):
        repo_loc = graphene_info.context.get_repository_location(repository_selector.location_name)
        if repo_loc.has_repository(repository_selector.repository_name):
            return graphene_info.schema.type_named("Repository")(
                repository=repo_loc.get_repository(repository_selector.repository_name),
                repository_location=repo_loc,
            )

    return graphene_info.schema.type_named("RepositoryNotFoundError")(
        repository_selector.location_name, repository_selector.repository_name
    )


@capture_dauphin_error
def fetch_repository_locations(graphene_info):
    check.inst_param(graphene_info, "graphene_info", ResolveInfo)

    nodes = []

    for location_name in graphene_info.context.repository_location_names:
        node = (
            graphene_info.schema.type_named("RepositoryLocation")(
                graphene_info.context.get_repository_location(location_name)
            )
            if graphene_info.context.has_repository_location(location_name)
            else graphene_info.schema.type_named("RepositoryLocationLoadFailure")(
                location_name, graphene_info.context.get_repository_location_error(location_name),
            )
        )
        nodes.append(node)

    return graphene_info.schema.type_named("RepositoryLocationConnection")(nodes=nodes)

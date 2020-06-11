from dagster_graphql.implementation.context import DagsterGraphQLContext
from dagster_graphql.schema import create_schema
from graphql import graphql

from dagster import check
from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.host_representation import InProcessRepositoryLocation
from dagster.core.instance import DagsterInstance


def execute_dagster_graphql(context, query, variables=None):
    result = graphql(
        create_schema(),
        query,
        context=context,
        variables=variables,
        allow_subscriptions=True,
        return_promise=False,
    )

    # has to check attr because in subscription case it returns AnonymousObservable
    if hasattr(result, 'errors') and result.errors:
        first_error = result.errors[0]
        if hasattr(first_error, 'original_error') and first_error.original_error:
            raise result.errors[0].original_error

        raise result.errors[0]

    return result


def execute_dagster_graphql_and_finish_runs(context, query, variables=None):
    result = execute_dagster_graphql(context, query, variables)
    context.drain_outstanding_executions()
    return result


def define_context_for_file(python_file, fn_name, instance):
    check.inst_param(instance, 'instance', DagsterInstance)
    return DagsterGraphQLContext(
        locations=[
            InProcessRepositoryLocation(ReconstructableRepository.for_file(python_file, fn_name))
        ],
        instance=instance,
    )


def define_subprocess_context_for_file(python_file, fn_name, instance):
    check.inst_param(instance, 'instance', DagsterInstance)
    return DagsterGraphQLContext(
        locations=[
            InProcessRepositoryLocation(ReconstructableRepository.for_file(python_file, fn_name))
        ],
        instance=instance,
    )


def define_context_for_repository_yaml(path, instance):
    check.inst_param(instance, 'instance', DagsterInstance)
    return DagsterGraphQLContext(
        locations=[
            InProcessRepositoryLocation(ReconstructableRepository.from_legacy_repository_yaml(path))
        ],
        instance=instance,
    )


def infer_repository(graphql_context):
    if len(graphql_context.repository_locations) == 1:
        # This is to account for having a single in process repository
        repository_location = graphql_context.repository_locations[0]
        repositories = repository_location.get_repositories()
        assert len(repositories) == 1
        return next(iter(repositories.values()))

    repository_location = graphql_context.get_repository_location('test')
    return repository_location.get_repository('test_repo')


def infer_repository_selector(graphql_context):
    if len(graphql_context.repository_locations) == 1:
        # This is to account for having a single in process repository
        repository_location = graphql_context.repository_locations[0]
        repositories = repository_location.get_repositories()
        assert len(repositories) == 1
        repository = next(iter(repositories.values()))
    else:
        repository_location = graphql_context.get_repository_location('test')
        repository = repository_location.get_repository('test_repo')

    return {
        'repositoryLocationName': repository_location.name,
        'repositoryName': repository.name,
    }


def infer_pipeline_selector(graphql_context, pipeline_name, solid_selection=None):
    selector = infer_repository_selector(graphql_context)
    selector.update({'pipelineName': pipeline_name, 'solidSelection': solid_selection})
    return selector


def infer_schedule_selector(graphql_context, schedule_name):
    selector = infer_repository_selector(graphql_context)
    selector.update({'scheduleName': schedule_name})
    return selector

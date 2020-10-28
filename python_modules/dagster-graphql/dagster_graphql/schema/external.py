from __future__ import absolute_import

from dagster import check
from dagster.core.host_representation import (
    ExternalRepository,
    ExternalRepositoryOrigin,
    ManagedGrpcPythonEnvRepositoryLocationHandle,
    RepositoryLocation,
)
from dagster.utils.error import SerializableErrorInfo
from dagster_graphql import dauphin
from dagster_graphql.implementation.fetch_solids import get_solid, get_solids
from dagster_graphql.schema.errors import DauphinPythonError


class DauphinRepository(dauphin.ObjectType):
    class Meta(object):
        name = "Repository"

    def __init__(self, repository, repository_location):
        self._repository = check.inst_param(repository, "repository", ExternalRepository)
        self._repository_location = check.inst_param(
            repository_location, "repository_location", RepositoryLocation
        )
        super(DauphinRepository, self).__init__(name=repository.name)

    id = dauphin.NonNull(dauphin.ID)
    name = dauphin.NonNull(dauphin.String)
    location = dauphin.NonNull("RepositoryLocation")
    pipelines = dauphin.non_null_list("Pipeline")
    usedSolids = dauphin.Field(dauphin.non_null_list("UsedSolid"))
    usedSolid = dauphin.Field("UsedSolid", name=dauphin.NonNull(dauphin.String))
    origin = dauphin.NonNull("RepositoryOrigin")
    partitionSets = dauphin.non_null_list("PartitionSet")
    scheduleDefinitions = dauphin.non_null_list("ScheduleDefinition")

    def resolve_id(self, _graphene_info):
        return self._repository.get_external_origin_id()

    def resolve_origin(self, graphene_info):
        origin = self._repository.get_external_origin()
        return graphene_info.schema.type_named("RepositoryOrigin")(origin)

    def resolve_location(self, graphene_info):
        return graphene_info.schema.type_named("RepositoryLocation")(self._repository_location)

    def resolve_scheduleDefinitions(self, graphene_info):

        schedules = self._repository.get_external_schedules()

        return sorted(
            [
                graphene_info.schema.type_named("ScheduleDefinition")(graphene_info, schedule)
                for schedule in schedules
            ],
            key=lambda schedule: schedule.name,
        )

    def resolve_pipelines(self, graphene_info):
        return sorted(
            [
                graphene_info.schema.type_named("Pipeline")(pipeline)
                for pipeline in self._repository.get_all_external_pipelines()
            ],
            key=lambda pipeline: pipeline.name,
        )

    def resolve_usedSolid(self, _graphene_info, name):
        return get_solid(self._repository, name)

    def resolve_usedSolids(self, _graphene_info):
        return get_solids(self._repository)

    def resolve_partitionSets(self, graphene_info):
        return (
            graphene_info.schema.type_named("PartitionSet")(self._repository.handle, partition_set)
            for partition_set in self._repository.get_external_partition_sets()
        )


class DauphinRepositoryOrigin(dauphin.ObjectType):
    class Meta(object):
        name = "RepositoryOrigin"

    repository_location_name = dauphin.NonNull(dauphin.String)
    repository_name = dauphin.NonNull(dauphin.String)
    repository_location_metadata = dauphin.non_null_list("RepositoryMetadata")

    def __init__(self, origin):
        self._origin = check.inst_param(origin, "origin", ExternalRepositoryOrigin)

    def resolve_repository_location_name(self, _graphene_info):
        return self._origin.repository_location_origin.location_name

    def resolve_repository_name(self, _graphene_info):
        return self._origin.repository_name

    def resolve_repository_location_metadata(self, graphene_info):
        metadata = self._origin.repository_location_origin.get_display_metadata()
        return [
            graphene_info.schema.type_named("RepositoryMetadata")(key=key, value=value)
            for key, value in metadata.items()
            if value is not None
        ]


class DauphinRepositoryMetadata(dauphin.ObjectType):
    class Meta(object):
        name = "RepositoryMetadata"

    key = dauphin.NonNull(dauphin.String)
    value = dauphin.NonNull(dauphin.String)


class DauphinRepositoryLocationOrLoadFailure(dauphin.Union):
    class Meta(object):
        name = "RepositoryLocationOrLoadFailure"
        types = ("RepositoryLocation", "RepositoryLocationLoadFailure")


class DauphinRepositoryLocation(dauphin.ObjectType):
    class Meta(object):
        name = "RepositoryLocation"

    id = dauphin.NonNull(dauphin.ID)
    name = dauphin.NonNull(dauphin.String)
    is_reload_supported = dauphin.NonNull(dauphin.Boolean)
    environment_path = dauphin.String()
    repositories = dauphin.non_null_list("Repository")

    def __init__(self, location):
        self._location = check.inst_param(location, "location", RepositoryLocation)
        environment_path = (
            location.location_handle.executable_path
            if isinstance(location.location_handle, ManagedGrpcPythonEnvRepositoryLocationHandle)
            else None
        )

        check.invariant(location.name is not None)

        super(DauphinRepositoryLocation, self).__init__(
            name=location.name,
            environment_path=environment_path,
            is_reload_supported=location.is_reload_supported,
        )

    def resolve_id(self, _):
        return self.name

    def resolve_repositories(self, graphene_info):
        return [
            graphene_info.schema.type_named("Repository")(repository, self._location)
            for repository in self._location.get_repositories().values()
        ]


class DauphinRepositoryLocationLoadFailure(dauphin.ObjectType):
    class Meta(object):
        name = "RepositoryLocationLoadFailure"

    id = dauphin.NonNull(dauphin.ID)
    name = dauphin.NonNull(dauphin.String)
    error = dauphin.NonNull("PythonError")

    def __init__(self, name, error):
        check.str_param(name, "name")
        check.inst_param(error, "error", SerializableErrorInfo)
        super(DauphinRepositoryLocationLoadFailure, self).__init__(
            name=name, error=DauphinPythonError(error)
        )

    def resolve_id(self, _):
        return self.name


class DauphinRepositoryConnection(dauphin.ObjectType):
    class Meta(object):
        name = "RepositoryConnection"

    nodes = dauphin.non_null_list("Repository")


class DauphinRepositoryLocationConnection(dauphin.ObjectType):
    class Meta(object):
        name = "RepositoryLocationConnection"

    nodes = dauphin.non_null_list("RepositoryLocationOrLoadFailure")

from abc import ABCMeta, abstractmethod
from contextlib import contextmanager

import pytest
import six
from dagster_graphql.implementation.context import DagsterGraphQLContext
from dagster_graphql.test.exploding_run_launcher import ExplodingRunLauncher

from dagster import check, file_relative_path, seven
from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.host_representation import (
    InProcessRepositoryLocation,
    PythonEnvRepositoryLocation,
    RepositoryLocationHandle,
)
from dagster.core.instance import DagsterInstance, InstanceType
from dagster.core.launcher.sync_in_memory_run_launcher import SyncInMemoryRunLauncher
from dagster.core.storage.event_log import InMemoryEventLogStorage
from dagster.core.storage.event_log.sqlite import ConsolidatedSqliteEventLogStorage
from dagster.core.storage.local_compute_log_manager import LocalComputeLogManager
from dagster.core.storage.root import LocalArtifactStorage
from dagster.core.storage.runs import InMemoryRunStorage
from dagster.core.storage.schedules.sqlite.sqlite_schedule_storage import SqliteScheduleStorage


def get_main_recon_repo():
    return ReconstructableRepository.from_legacy_repository_yaml(
        file_relative_path(__file__, 'repo.yaml')
    )


class MarkedManager:
    '''
    MarkedManagers are passed to GraphQLContextVariants. They contain
    a contextmanager function "manager_fn" that yield the relevant
    instace, and it includes marks that will be applied to any
    context-variant-driven test case that includes this MarkedManager.

    See InstanceManagers for an example construction.

    See GraphQLContextVariant for further information
    '''

    def __init__(self, manager_fn, marks):
        self.manager_fn = check.callable_param(manager_fn, 'manager_fn')
        self.marks = check.list_param(marks, 'marks')


class InstanceManagers:
    @staticmethod
    def in_memory_instance():
        @contextmanager
        def _in_memory_instance():
            with seven.TemporaryDirectory() as temp_dir:
                yield DagsterInstance(
                    instance_type=InstanceType.EPHEMERAL,
                    local_artifact_storage=LocalArtifactStorage(temp_dir),
                    run_storage=InMemoryRunStorage(),
                    event_storage=InMemoryEventLogStorage(),
                    compute_log_manager=LocalComputeLogManager(temp_dir),
                    run_launcher=SyncInMemoryRunLauncher(),
                    schedule_storage=SqliteScheduleStorage.from_local(temp_dir),
                )

        return MarkedManager(_in_memory_instance, [Marks.in_memory_instance])

    @staticmethod
    def readonly_in_memory_instance():
        @contextmanager
        def _readonly_in_memory_instance():
            with seven.TemporaryDirectory() as temp_dir:
                yield DagsterInstance(
                    instance_type=InstanceType.EPHEMERAL,
                    local_artifact_storage=LocalArtifactStorage(temp_dir),
                    run_storage=InMemoryRunStorage(),
                    event_storage=InMemoryEventLogStorage(),
                    compute_log_manager=LocalComputeLogManager(temp_dir),
                    run_launcher=ExplodingRunLauncher(),
                    schedule_storage=SqliteScheduleStorage.from_local(temp_dir),
                )

        return MarkedManager(
            _readonly_in_memory_instance, [Marks.in_memory_instance, Marks.readonly],
        )

    @staticmethod
    def readonly_sqlite_instance():
        @contextmanager
        def _readonly_sqlite_instance():
            with seven.TemporaryDirectory() as temp_dir:
                instance = DagsterInstance.local_temp(
                    temp_dir,
                    overrides={
                        'scheduler': {
                            'module': 'dagster.utils.test',
                            'class': 'FilesystemTestScheduler',
                            'config': {'base_dir': temp_dir},
                        },
                        'run_launcher': {
                            'module': 'dagster_graphql.test.exploding_run_launcher',
                            'class': 'ExplodingRunLauncher',
                        },
                    },
                )
                yield instance

        return MarkedManager(_readonly_sqlite_instance, [Marks.sqlite_instance, Marks.readonly])

    @staticmethod
    def sqlite_instance_with_sync_run_launcher():
        @contextmanager
        def _sqlite_instance():
            with seven.TemporaryDirectory() as temp_dir:
                instance = DagsterInstance.local_temp(
                    temp_dir,
                    overrides={
                        'scheduler': {
                            'module': 'dagster.utils.test',
                            'class': 'FilesystemTestScheduler',
                            'config': {'base_dir': temp_dir},
                        },
                        'run_launcher': {
                            'module': 'dagster.core.launcher.sync_in_memory_run_launcher',
                            'class': 'SyncInMemoryRunLauncher',
                        },
                    },
                )
                yield instance

        return MarkedManager(_sqlite_instance, [Marks.sqlite_instance, Marks.sync_run_launcher])

    @staticmethod
    def sqlite_instance_with_cli_api_run_launcher():
        @contextmanager
        def _sqlite_instance_with_cli_api_hijack():
            with seven.TemporaryDirectory() as temp_dir:
                instance = DagsterInstance.local_temp(
                    temp_dir,
                    overrides={
                        'scheduler': {
                            'module': 'dagster.utils.test',
                            'class': 'FilesystemTestScheduler',
                            'config': {'base_dir': temp_dir},
                        },
                        'run_launcher': {
                            'module': 'dagster.core.launcher',
                            'class': 'CliApiRunLauncher',
                        },
                    },
                )
                try:
                    yield instance
                finally:
                    instance.run_launcher.join()

        return MarkedManager(
            _sqlite_instance_with_cli_api_hijack,
            [Marks.sqlite_instance, Marks.cli_api_run_launcher],
        )

    @staticmethod
    def asset_aware_sqlite_instance():
        @contextmanager
        def _sqlite_asset_instance():
            with seven.TemporaryDirectory() as temp_dir:
                instance = DagsterInstance(
                    instance_type=InstanceType.EPHEMERAL,
                    local_artifact_storage=LocalArtifactStorage(temp_dir),
                    run_storage=InMemoryRunStorage(),
                    event_storage=ConsolidatedSqliteEventLogStorage(temp_dir),
                    compute_log_manager=LocalComputeLogManager(temp_dir),
                    run_launcher=SyncInMemoryRunLauncher(),
                )
                yield instance

        return MarkedManager(_sqlite_asset_instance, [Marks.asset_aware_instance])


class EnvironmentManagers:
    @staticmethod
    def user_code_in_host_process():
        @contextmanager
        def _mgr_fn(recon_repo):
            check.inst_param(recon_repo, 'recon_repo', ReconstructableRepository)
            yield [InProcessRepositoryLocation(recon_repo=recon_repo)]

        return MarkedManager(_mgr_fn, [Marks.hosted_user_process_env])

    @staticmethod
    def out_of_process():
        @contextmanager
        def _mgr_fn(recon_repo):
            '''Goes out of process but same process as host process'''
            check.inst_param(recon_repo, 'recon_repo', ReconstructableRepository)

            # this is "ok" because we know the test host process containers the user code
            repo_name = recon_repo.get_definition().name
            yield [
                PythonEnvRepositoryLocation(
                    RepositoryLocationHandle.create_out_of_process_location(
                        location_name='test',
                        repository_code_pointer_dict={repo_name: recon_repo.pointer},
                    )
                )
            ]

        return MarkedManager(_mgr_fn, [Marks.out_of_process_env])

    @staticmethod
    def multi_location():
        @contextmanager
        def _mgr_fn(recon_repo):
            '''Goes out of process but same process as host process'''
            check.inst_param(recon_repo, 'recon_repo', ReconstructableRepository)

            empty_repo = ReconstructableRepository.from_legacy_repository_yaml(
                file_relative_path(__file__, 'empty_repo.yaml')
            )

            yield [
                PythonEnvRepositoryLocation(
                    RepositoryLocationHandle.create_out_of_process_location(
                        location_name='test',
                        repository_code_pointer_dict={
                            recon_repo.get_definition().name: recon_repo.pointer
                        },
                    )
                ),
                InProcessRepositoryLocation(empty_repo),
                PythonEnvRepositoryLocation(
                    RepositoryLocationHandle.create_out_of_process_location(
                        location_name='empty_repo',
                        repository_code_pointer_dict={
                            empty_repo.get_definition().name: empty_repo.pointer
                        },
                    )
                ),
            ]

        return MarkedManager(_mgr_fn, [Marks.multi_location])


class Marks:
    # Instance type makes
    in_memory_instance = pytest.mark.in_memory_instance
    sqlite_instance = pytest.mark.sqlite_instance

    # Run launcher variants
    sync_run_launcher = pytest.mark.sync_run_launcher
    cli_api_run_launcher = pytest.mark.cli_api_run_launcher
    readonly = pytest.mark.readonly

    # Repository Location marks
    hosted_user_process_env = pytest.mark.hosted_user_process_env
    out_of_process_env = pytest.mark.out_of_process_env
    multi_location = pytest.mark.multi_location

    # Asset-aware sqlite variants
    asset_aware_instance = pytest.mark.asset_aware_instance

    # Common mark to all test suite tests
    graphql_context_test_suite = pytest.mark.graphql_context_test_suite


def none_manager():
    @contextmanager
    def _yield_none(*_args, **_kwargs):
        yield None

    return MarkedManager(_yield_none, [])


class GraphQLContextVariant:
    '''
    An instance of this class represents a context variant that will be run
    against *every* method in the test class, defined as a class
    created by inheriting from make_graphql_context_test_suite.

    It comes with a number of static methods with prebuilt context variants.
    e.g. in_memory_in_process_start

    One can also make bespoke context variants, provided you configure it properly
    with MarkedMembers that produce its members.

    Args:

    marked_instance_mgr (MarkedManager): The manager_fn
    within it must be a contextmanager that takes zero arguments and yields
    a DagsterInstance

    See InstanceManagers for examples

    marked_environment_mgr (MarkedManager): The manager_fn with in
    must be a contextmanager takes a default ReconstructableRepo and
    yields a list of RepositoryLocation.

    See EnvironmentManagers for examples

    test_id [Optional] (str): This assigns a test_id to test parameterized with this
    variant. This is highly convenient for running a particular variant across
    the entire test suite, without running all the other variants.

    e.g.
    pytest python_modules/dagster-graphql/dagster_graphql_tests/ -s -k in_memory_in_process_start

    Will run all tests that use the in_memory_in_process_start, which will get a lot
    of code coverage while being very fast to run.

    All tests managed by this system are marked with "graphql_context_test_suite".
    '''

    def __init__(
        self, marked_instance_mgr, marked_environment_mgr, test_id=None,
    ):
        self.marked_instance_mgr = check.inst_param(
            marked_instance_mgr, 'marked_instance_mgr', MarkedManager
        )
        self.marked_environment_mgr = check.inst_param(
            marked_environment_mgr, 'marked_environment_mgr', MarkedManager
        )
        self.test_id = check.opt_str_param(test_id, 'test_id')
        self.marks = marked_instance_mgr.marks + marked_environment_mgr.marks

    @property
    def instance_mgr(self):
        return self.marked_instance_mgr.manager_fn

    @property
    def environment_mgr(self):
        return self.marked_environment_mgr.manager_fn

    @staticmethod
    def in_memory_instance_in_process_env():
        '''
        Good for tests with read-only metadata queries. Does not work
        if you have to go through the run launcher.
        '''
        return GraphQLContextVariant(
            InstanceManagers.in_memory_instance(),
            EnvironmentManagers.user_code_in_host_process(),
            test_id='in_memory_instance_in_process_env',
        )

    @staticmethod
    def in_memory_instance_out_of_process_env():
        '''
        Good for tests with read-only metadata queries. Does not work
        if you have to go through the run launcher.
        '''
        return GraphQLContextVariant(
            InstanceManagers.in_memory_instance(),
            EnvironmentManagers.out_of_process(),
            test_id='in_memory_instance_out_of_process_env',
        )

    @staticmethod
    def sqlite_with_sync_run_launcher_in_process_env():
        return GraphQLContextVariant(
            InstanceManagers.sqlite_instance_with_sync_run_launcher(),
            EnvironmentManagers.user_code_in_host_process(),
            test_id='sqlite_with_sync_run_launcher_in_process_env',
        )

    @staticmethod
    def sqlite_with_cli_api_run_launcher_in_process_env():
        return GraphQLContextVariant(
            InstanceManagers.sqlite_instance_with_cli_api_run_launcher(),
            EnvironmentManagers.user_code_in_host_process(),
            test_id='sqlite_with_cli_api_run_launcher_in_process_env',
        )

    @staticmethod
    def readonly_sqlite_instance_in_process_env():
        return GraphQLContextVariant(
            InstanceManagers.readonly_sqlite_instance(),
            EnvironmentManagers.user_code_in_host_process(),
            test_id='readonly_sqlite_instance_in_process_env',
        )

    @staticmethod
    def readonly_sqlite_instance_out_of_process_env():
        return GraphQLContextVariant(
            InstanceManagers.readonly_sqlite_instance(),
            EnvironmentManagers.out_of_process(),
            test_id='readonly_sqlite_instance_out_of_process_env',
        )

    @staticmethod
    def readonly_sqlite_instance_multi_location():
        return GraphQLContextVariant(
            InstanceManagers.readonly_sqlite_instance(),
            EnvironmentManagers.multi_location(),
            test_id='readonly_sqlite_instance_multi_location',
        )

    @staticmethod
    def readonly_in_memory_instance_in_process_env():
        return GraphQLContextVariant(
            InstanceManagers.readonly_in_memory_instance(),
            EnvironmentManagers.user_code_in_host_process(),
            test_id='readonly_in_memory_instance_in_process_env',
        )

    @staticmethod
    def readonly_in_memory_instance_out_of_process_env():
        return GraphQLContextVariant(
            InstanceManagers.readonly_in_memory_instance(),
            EnvironmentManagers.out_of_process(),
            test_id='readonly_in_memory_instance_out_of_process_env',
        )

    @staticmethod
    def readonly_in_memory_instance_multi_location():
        return GraphQLContextVariant(
            InstanceManagers.readonly_in_memory_instance(),
            EnvironmentManagers.multi_location(),
            test_id='readonly_in_memory_instance_multi_location',
        )

    @staticmethod
    def asset_aware_sqlite_instance_in_process_env():
        return GraphQLContextVariant(
            InstanceManagers.asset_aware_sqlite_instance(),
            EnvironmentManagers.user_code_in_host_process(),
            test_id='asset_aware_instance_in_process_env',
        )

    @staticmethod
    def all_variants():
        '''
        There is a test case that keeps this up-to-date. If you add a static
        method that returns a GraphQLContextVariant you have to add it to this
        list in order for tests to pass.
        '''
        return [
            GraphQLContextVariant.in_memory_instance_in_process_env(),
            GraphQLContextVariant.in_memory_instance_out_of_process_env(),
            GraphQLContextVariant.sqlite_with_sync_run_launcher_in_process_env(),
            GraphQLContextVariant.sqlite_with_cli_api_run_launcher_in_process_env(),
            GraphQLContextVariant.readonly_in_memory_instance_in_process_env(),
            GraphQLContextVariant.readonly_in_memory_instance_out_of_process_env(),
            GraphQLContextVariant.readonly_in_memory_instance_multi_location(),
            GraphQLContextVariant.readonly_sqlite_instance_in_process_env(),
            GraphQLContextVariant.readonly_sqlite_instance_out_of_process_env(),
            GraphQLContextVariant.readonly_sqlite_instance_multi_location(),
            GraphQLContextVariant.asset_aware_sqlite_instance_in_process_env(),
        ]

    @staticmethod
    def all_executing_variants():
        return [
            GraphQLContextVariant.in_memory_instance_in_process_env(),
            GraphQLContextVariant.sqlite_with_sync_run_launcher_in_process_env(),
            GraphQLContextVariant.sqlite_with_cli_api_run_launcher_in_process_env(),
        ]

    @staticmethod
    def all_readonly_variants():
        '''
        Return all readonly variants. If you try to start or launch these will error
        '''
        return _variants_with_mark(GraphQLContextVariant.all_variants(), pytest.mark.readonly)

    @staticmethod
    def legacy_all_readonly_variants():
        '''
        Return all readonly variants that are in process and single location.
        If you try to start or launch these will error
        '''
        return _variants_without_marks(
            _variants_with_mark(GraphQLContextVariant.all_variants(), pytest.mark.readonly),
            [pytest.mark.multi_location],
        )


def _variants_with_mark(variants, mark):
    def _yield_all():
        for variant in variants:
            if mark in variant.marks:
                yield variant

    return list(_yield_all())


def _variants_without_marks(variants, marks):
    def _yield_all():
        for variant in variants:
            if all(mark not in variant.marks for mark in marks):
                yield variant

    return list(_yield_all())


@contextmanager
def manage_graphql_context(context_variant, recon_repo=None):
    recon_repo = recon_repo if recon_repo else get_main_recon_repo()
    with context_variant.instance_mgr() as instance:
        with context_variant.environment_mgr(recon_repo) as environments:
            yield DagsterGraphQLContext(instance=instance, locations=environments)


class _GraphQLContextTestSuite(six.with_metaclass(ABCMeta)):
    @abstractmethod
    def yield_graphql_context(self, request):
        pass

    @abstractmethod
    def recon_repo(self):
        pass

    @contextmanager
    def graphql_context_for_request(self, request):
        check.param_invariant(
            isinstance(request.param, GraphQLContextVariant),
            'request',
            'params in fixture must be List[GraphQLContextVariant]',
        )
        with manage_graphql_context(request.param, self.recon_repo()) as graphql_context:
            yield graphql_context


def graphql_context_variants_fixture(context_variants):
    check.list_param(context_variants, 'context_variants', of_type=GraphQLContextVariant)

    def _wrap(fn):
        return pytest.fixture(
            name='graphql_context',
            params=[
                pytest.param(
                    context_variant,
                    id=context_variant.test_id,
                    marks=context_variant.marks + [Marks.graphql_context_test_suite],
                )
                for context_variant in context_variants
            ],
        )(fn)

    return _wrap


def make_graphql_context_test_suite(context_variants, recon_repo=None):
    '''
    Arguments:

    runs (List[GraphQLContextVariant]): List of runs to run per test in this class.
    recon_repo (ReconstructableRepository): Repository to run against. Defaults
    to "define_repository" in setup.py

    This is the base class factory for test suites in the dagster-graphql test.

    The goal of this suite is to make it straightforward to run tests
    against multiple graphql_contexts, have a coherent lifecycle for those
    contexts.

    GraphQLContextVariant has a number of static methods to provide common run configurations
    as well as common groups of run configuration

    One can also make bespoke GraphQLContextVariants which specific implementations
    of DagsterInstance, RepositoryLocation, and so forth. See that class
    for more details.

Example:

class TestAThing(
    make_graphql_context_test_suite(
        context_variants=[GraphQLContextVariant.in_memory_in_process_start()]
    )
):
    def test_graphql_context_exists(self, graphql_context):
        assert graphql_context
    '''
    check.list_param(context_variants, 'context_variants', of_type=GraphQLContextVariant)
    recon_repo = check.inst_param(
        recon_repo if recon_repo else get_main_recon_repo(), 'recon_repo', ReconstructableRepository
    )

    class _SpecificTestSuiteBase(_GraphQLContextTestSuite):
        @graphql_context_variants_fixture(context_variants=context_variants)
        def yield_graphql_context(self, request):
            with self.graphql_context_for_request(request) as graphql_context:
                yield graphql_context

        def recon_repo(self):
            return recon_repo

    return _SpecificTestSuiteBase


ReadonlyGraphQLContextTestMatrix = make_graphql_context_test_suite(
    context_variants=GraphQLContextVariant.all_readonly_variants()
)

LegacyReadonlyGraphQLContextTestMatrix = make_graphql_context_test_suite(
    context_variants=GraphQLContextVariant.legacy_all_readonly_variants()
)

ExecutingGraphQLContextTestMatrix = make_graphql_context_test_suite(
    context_variants=GraphQLContextVariant.all_executing_variants()
)

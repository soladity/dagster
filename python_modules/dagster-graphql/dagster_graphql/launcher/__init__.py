from future.standard_library import install_aliases  # isort:skip

install_aliases()  # isort:skip

import requests
from dagster_graphql.client.query import START_PIPELINE_EXECUTION_MUTATION
from dagster_graphql.client.util import execution_params_from_pipeline_run

from dagster import Bool, Field, String, check, seven
from dagster.core.errors import DagsterLaunchFailedError
from dagster.core.launcher import RunLauncher
from dagster.core.serdes import ConfigurableClass, ConfigurableClassData
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.types.config.field_utils import NamedDict
from dagster.seven import urljoin, urlparse


class RemoteDagitRunLauncher(RunLauncher, ConfigurableClass):
    def __init__(self, address, inst_data=None):
        self._inst_data = check.opt_inst_param(inst_data, 'inst_data', ConfigurableClassData)
        self._address = check.str_param(address, 'address')
        self._handle = None
        self._instance = None

        parsed_url = urlparse(address)
        check.invariant(
            parsed_url.scheme and parsed_url.netloc,
            'Address {address} is not a valid URL. Host URL should include scheme ie http://localhost'.format(
                address=self._address
            ),
        )

    @classmethod
    def config_type(cls):
        return NamedDict('RemoteDagitExecutionServerConfig', {'address': Field(String)},)

    @classmethod
    def from_config_value(cls, inst_data, config_value, **kwargs):
        return cls(address=config_value['address'], inst_data=inst_data,)

    @property
    def inst_data(self):
        return self._inst_data

    def start(self, handle, instance):
        self._handle = handle
        self._instance = instance

    def stop(self):
        self._handle = None
        self._instance = None

    def validate(self):
        sanity_check = requests.get(urljoin(self._address, '/dagit_info'))
        sanity_check.raise_for_status()
        check.invariant(
            'dagit' in sanity_check.text,
            'Host {host} failed sanity check. It is not a dagit server.'.format(host=self._address),
        )

    def launch_run(self, run):
        execution_params = execution_params_from_pipeline_run(run)
        variables = {'executionParams': execution_params.to_graphql_input()}
        response = requests.post(
            urljoin(self._address, '/graphql'),
            params={
                'query': START_PIPELINE_EXECUTION_MUTATION,
                'variables': seven.json.dumps(variables),
            },
        )
        response.raise_for_status()
        result = response.json()['data']['startPipelineExecution']

        if result['__typename'] == 'StartPipelineExecutionSuccess':
            return run.run_with_status(PipelineRunStatus(result['run']['status']))

        raise DagsterLaunchFailedError(
            'Failed to launch run with {cls} targeting {address}:\n{result}'.format(
                cls=self.__class__.__name__, address=self._address, result=result
            )
        )

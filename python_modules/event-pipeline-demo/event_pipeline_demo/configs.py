'''Spark Configuration

In this file we define the key configuration parameters for submitting Spark jobs. Spark can be run
in a variety of deployment contexts. See the Spark documentation at
https://spark.apache.org/docs/latest/submitting-applications.html for a more in-depth summary of
Spark deployment contexts and configuration.
'''
import itertools
import os

from dagster import Dict, Field, List, Path, String

from .types import SparkDeployMode
from .configs_spark import spark_config


def parse_spark_config(spark_conf):
    '''For each key-value pair in spark conf, we need to pass to CLI in format:

        --conf "key=value"
    '''

    def flatten_dict(d):
        def _flatten_dict(d, result, key_path=None):
            '''Iterates an arbitrarily nested dictionary and yield dot-notation key:value tuples.

            {'foo': {'bar': 3, 'baz': 1}, {'other': {'key': 1}} =>
                [('foo.bar', 3), ('foo.baz', 1), ('other.key', 1)]

            '''
            for k, v in d.items():
                new_key_path = (key_path or []) + [k]
                if isinstance(v, dict):
                    _flatten_dict(v, result, new_key_path)
                else:
                    result.append(('.'.join(new_key_path), v))

        result = []
        _flatten_dict(d, result)
        return result

    spark_conf_list = flatten_dict(spark_conf)
    return list(
        itertools.chain.from_iterable([('--conf', '{}={}'.format(*c)) for c in spark_conf_list])
    )


def define_spark_config():
    main_class = Field(
        String,
        description='The entry point for your application (e.g. org.apache.spark.examples.SparkPi)',
        is_optional=False,
    )

    master_url = Field(
        String,
        description='The master URL for the cluster (e.g. spark://23.195.26.187:7077)',
        is_optional=False,
    )

    deploy_mode = Field(
        SparkDeployMode,
        description='''Whether to deploy your driver on the worker nodes (cluster) or locally as an
        external client (client) (default: client). A common deployment strategy is to submit your
        application from a gateway machine that is physically co-located with your worker machines
        (e.g. Master node in a standalone EC2 cluster). In this setup, client mode is appropriate. 
        In client mode, the driver is launched directly within the spark-submit process which acts 
        as a client to the cluster. The input and output of the application is attached to the 
        console. Thus, this mode is especially suitable for applications that involve the REPL (e.g.
        Spark shell).''',
        is_optional=True,
    )

    application_jar = Field(
        Path,
        description='''Path to a bundled jar including your application and all
                        dependencies. The URL must be globally visible inside of your cluster, for
                        instance, an hdfs:// path or a file:// path that is present on all nodes.
                        ''',
        is_optional=False,
    )

    application_arguments = Field(
        String,
        description='Arguments passed to the main method of your main class, if any',
        is_optional=True,
    )

    spark_home = Field(
        String,
        description='The path to your spark installation. Defaults to $SPARK_HOME',
        is_optional=True,
        default_value=os.environ.get('SPARK_HOME'),
    )

    spark_outputs = Field(List(String), description='The outputs that this Spark job will produce')

    return Field(
        Dict(
            # See the Spark documentation for reference:
            # https://spark.apache.org/docs/latest/submitting-applications.html
            fields={
                'main_class': main_class,
                'master_url': master_url,
                'deploy_mode': deploy_mode,
                'application_jar': application_jar,
                'spark_conf': spark_config(),
                'spark_home': spark_home,
                'application_arguments': application_arguments,
                'spark_outputs': spark_outputs,
            }
        )
    )

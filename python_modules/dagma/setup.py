import sys
import os

from setuptools import find_packages, setup

# pylint: disable=E0401, W0611
if sys.version_info[0] < 3:
    import __builtin__ as builtins
else:
    import builtins


def _long_description():
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, 'README.rst'), 'r') as fh:
        return fh.read()


VERSION = {}
with open("dagma/version.py") as fp:
    exec(fp.read(), VERSION)  # pylint: disable=W0122

setup(
    name='dagma',
    version=VERSION['__version__'],
    author='Elementl',
    license='Apache-2.0',
    description='Dagma is an experimental AWS Lambda-based execution engine for dagster pipelines.',
    long_description=_long_description(),
    long_description_content_type='text/markdown',
    url='https://github.com/dagster-io/dagster',
    classifiers=[
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
    ],
    packages=find_packages(exclude=['tests']),
    install_requires=[
        'boto3==1.9.67',
        'cloudpickle==0.3.1',
        (
            'dagster @ git+https://github.com/dagster-io/dagster.git'
            '@lambda_engine#egg=dagster&subdirectory=python_modules/dagster'
        ),
        'glob2==0.6',
    ],
)

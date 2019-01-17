import argparse
import sys
import os

from setuptools import find_packages, setup

# pylint: disable=E0401, W0611
if sys.version_info[0] < 3:
    import __builtin__ as builtins
else:
    import builtins


def long_description():
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, 'README.rst'), 'r') as fh:
        return fh.read()


def get_version(name):
    version = {}
    with open("dagster/version.py") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    if name == 'dagster':
        return version['__version__']
    else:
        return version['__version__'] + version['__nightly__']


parser = argparse.ArgumentParser()
parser.add_argument('--nightly', action='store_true')


def _do_setup(name='dagster'):
    setup(
        name=name,
        version=get_version(name),
        author='Elementl',
        license='Apache-2.0',
        description='Dagster is an opinionated programming model for data pipelines.',
        long_description=long_description(),
        long_description_content_type='text/markdown',
        url='https://github.com/dagster-io/dagster',
        classifiers=[
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'License :: OSI Approved :: Apache Software License',
            'Operating System :: OS Independent',
        ],
        packages=find_packages(exclude=['dagster_tests']),
        install_requires=[
            # standard python 2/3 compatability things
            'enum34>=1.1.6',
            'future>=0.16.0',
            'funcsigs>=1.0.2',
            'contextlib2>=0.5.5',
            # cli
            'click>=6.7',
            'coloredlogs>=10.0',
            'graphviz>=0.8.3',
            'pyyaml>=3.12',
            # core (not explicitly expressed atm)
            'six>=1.11.0',
            'toposort>=1.5',
            # dev/test - Installed via dev-requirements.txt
            # 'pylint>=1.8.4',
            # 'pytest>=3.5.1',
            # 'recommonmark>=0.4.0',
            # 'rope>=0.10.7',
            # 'snapshottest==0.5.0',
            # 'Sphinx>=1.7.5',
            # 'sphinx-autobuild>=0.7.1',
            # 'yapf>=0.22.0',
            # 'twine>=1.11.0',
            # 'pre-commit'>=1.10.1',
        ],
        extras_require={":python_version>'3'": ["reloader>=0.6"]},
        entry_points={"console_scripts": ['dagster = dagster.cli:main']},
    )


if __name__ == '__main__':
    parsed, unparsed = parser.parse_known_args()
    sys.argv = [sys.argv[0]] + unparsed
    if parsed.nightly:
        _do_setup('dagster-nightly')
    else:
        _do_setup('dagster')

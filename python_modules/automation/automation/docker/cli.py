import os
import subprocess
import sys

import click
from automation.git import git_repo_root

from dagster import check

from .dagster_docker import DagsterDockerImage
from .ecr import ensure_ecr_login
from .image_defs import get_image, list_images
from .utils import current_time_str

CLI_HELP = '''This CLI is used for building the various Dagster images we use in test
'''


@click.group(help=CLI_HELP)
def cli():
    pass


@cli.command()
def list():  # pylint: disable=redefined-builtin
    for image in list_images():
        print(image)


@cli.command()
@click.option('--name', required=True, help='Name of image to build')
@click.option(
    '-t',
    '--timestamp',
    type=click.STRING,
    required=False,
    default=current_time_str(),
    help='Timestamp to build in format 2020-07-11T040642 (defaults to now UTC)',
)
@click.option('-v', '--python-version', type=click.STRING, required=True)
def build(name, timestamp, python_version):
    get_image(name).build(timestamp, python_version)


@cli.command()
@click.option('--name', required=True, help='Name of image to build')
@click.option(
    '-t',
    '--timestamp',
    type=click.STRING,
    required=False,
    default=current_time_str(),
    help='Timestamp to build in format 2020-07-11T040642 (defaults to now UTC)',
)
def build_all(name, timestamp):
    '''Build all supported python versions for image'''
    image = get_image(name)
    for python_version in image.python_versions:
        image.build(timestamp, python_version)


@cli.command()
@click.option('--name', required=True, help='Name of image to build')
@click.option('-v', '--python-version', type=click.STRING, required=True)
def push(name, python_version):
    ensure_ecr_login()
    get_image(name).push(python_version)


@cli.command()
@click.option('--name', required=True, help='Name of image to build')
def push_all(name):
    ensure_ecr_login()
    image = get_image(name)
    for python_version in image.python_versions:
        image.push(python_version)


@cli.command()
@click.option(
    '-t', '--snap-type', required=True, help='Whether to build integration or unit snapshots'
)
def snapshot(snap_type):
    '''Snapshot Python dependencies for the interation image.
    '''
    if snap_type == 'integration':
        image = DagsterDockerImage('buildkite-integration-snapshot-builder')
        output_path = 'buildkite-integration'
    elif snap_type == 'unit':
        image = DagsterDockerImage('buildkite-unit-snapshot-builder')
        output_path = 'buildkite-unit'
    else:
        raise Exception('Unrecognized snapshot type')

    for python_version in image.python_versions:
        reqs_path = os.path.join(
            git_repo_root(),
            'python_modules',
            'automation',
            'automation',
            'docker',
            'images',
            output_path,
            'snapshot-reqs-{python_version}.txt'.format(python_version=python_version),
        )

        retval = subprocess.call(
            'docker run {image} pip freeze --exclude-editable > {reqs}'.format(
                image=image.local_image(python_version), reqs=reqs_path
            ),
            stderr=sys.stderr,
            stdout=sys.stdout,
            shell=True,
        )
        check.invariant(retval == 0)


def main():
    click_cli = click.CommandCollection(sources=[cli], help=CLI_HELP)
    click_cli()


if __name__ == '__main__':
    main()

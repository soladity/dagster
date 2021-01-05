import click
from dagster import __version__ as current_dagster_version
from dagster import check

from .dagster_docker import DagsterDockerImage
from .ecr import ensure_ecr_login
from .image_defs import get_image, list_images
from .utils import current_time_str, execute_docker_push, execute_docker_tag

CLI_HELP = """This CLI is used for building the various Dagster images we use in test
"""


@click.group(help=CLI_HELP)
def cli():
    pass


@cli.command()
def list():  # pylint: disable=redefined-builtin
    for image in list_images():
        print(image.image)  # pylint: disable=print-call


@cli.command()
@click.option("--name", required=True, help="Name of image to build")
@click.option(
    "--dagster-version",
    required=True,
    help="Version of image to build, must match current dagster version",
)
@click.option(
    "-t",
    "--timestamp",
    type=click.STRING,
    required=False,
    default=current_time_str(),
    help="Timestamp to build in format 2020-07-11T040642 (defaults to now UTC)",
)
@click.option("-v", "--python-version", type=click.STRING, required=True)
def build(name, dagster_version, timestamp, python_version):
    get_image(name).build(timestamp, dagster_version, python_version)


@cli.command()
@click.option("--name", required=True, help="Name of image to build")
@click.option(
    "--dagster-version",
    required=True,
    help="Version of image to build, must match current dagster version",
)
@click.option(
    "-t",
    "--timestamp",
    type=click.STRING,
    required=False,
    default=current_time_str(),
    help="Timestamp to build in format 2020-07-11T040642 (defaults to now UTC)",
)
def build_all(name, dagster_version, timestamp):
    """Build all supported python versions for image"""
    image = get_image(name)

    for python_version in image.python_versions:
        image.build(timestamp, dagster_version, python_version)


@cli.command()
@click.option("--name", required=True, help="Name of image to push")
@click.option("-v", "--python-version", type=click.STRING, required=True)
@click.option("-v", "--custom-tag", type=click.STRING, required=False)
def push(name, python_version, custom_tag):
    ensure_ecr_login()
    get_image(name).push(python_version, custom_tag=custom_tag)


@cli.command()
@click.option("--name", required=True, help="Name of image to push")
def push_all(name):
    ensure_ecr_login()
    image = get_image(name)
    for python_version in image.python_versions:
        image.push(python_version)


@cli.command()
@click.option("--name", required=True, help="Name of image to push")
@click.option(
    "--dagster-version",
    required=True,
    help="Version of image to push, must match current dagster version",
)
def push_dockerhub(name, dagster_version):
    """Used for pushing k8s images to Docker Hub. Must be logged in to Docker Hub for this to
    succeed.
    """

    check.invariant(
        dagster_version == current_dagster_version,
        desc="Current dagster version ({}) does not match provided arg ({})".format(
            current_dagster_version, dagster_version
        ),
    )

    image = DagsterDockerImage(name)

    python_version = next(iter(image.python_versions))

    local_image = image.local_image(python_version)

    # Tag image as Dagster version (plan to release this image w/ Dagster releases)
    image_with_dagster_version_tag = "dagster/{image}:{tag}".format(
        image=name, tag=current_dagster_version
    )
    execute_docker_tag(local_image, image_with_dagster_version_tag)
    execute_docker_push(image_with_dagster_version_tag)

    # Also push latest tag
    latest_tag = "dagster/{}:latest".format(name)
    execute_docker_tag(local_image, latest_tag)
    execute_docker_push(latest_tag)


def main():
    click_cli = click.CommandCollection(sources=[cli], help=CLI_HELP)
    click_cli()


if __name__ == "__main__":
    main()

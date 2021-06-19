from typing import Dict

from setuptools import find_packages, setup  # type: ignore


def get_version() -> str:
    version: Dict[str, str] = {}
    with open("dagster_celery_docker/version.py") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    return version["__version__"]


if __name__ == "__main__":
    ver = get_version()
    # dont pin dev installs to avoid pip dep resolver issues
    pin = "" if ver == "dev" else f"=={ver}"
    setup(
        name="dagster-celery-docker",
        version=ver,
        author="Elementl",
        license="Apache-2.0",
        description="A Dagster integration for celery-docker",
        url="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-celery-docker",
        classifiers=[
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: OS Independent",
        ],
        packages=find_packages(exclude=["test"]),
        install_requires=[
            f"dagster{pin}",
            f"dagster-celery{pin}",
            f"dagster-graphql{pin}",
            "docker",
        ],
        zip_safe=False,
    )

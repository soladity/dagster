from typing import Dict

from setuptools import find_packages, setup  # type: ignore


def get_version() -> str:
    version: Dict[str, str] = {}
    with open("dagster_postgres/version.py") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    return version["__version__"]


if __name__ == "__main__":
    setup(
        name="dagster-postgres",
        version=get_version(),
        author="Elementl",
        author_email="hello@elementl.com",
        license="Apache-2.0",
        description="A Dagster integration for postgres",
        url="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-postgres",
        classifiers=[
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: OS Independent",
        ],
        packages=find_packages(exclude=["test"]),
        package_data={
            "dagster-postgres": [
                "dagster_postgres/event_log/alembic/*",
                "dagster_postgres/run_storage/alembic/*",
                "dagster_postgres/schedule_storage/alembic/*",
            ]
        },
        include_package_data=True,
        install_requires=["dagster", "psycopg2-binary"],
        zip_safe=False,
    )

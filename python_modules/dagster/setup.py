from setuptools import find_packages, setup


def long_description():
    return """
## Dagster
Dagster is a data orchestrator for machine learning, analytics, and ETL.

Dagster lets you define pipelines in terms of the data flow between reusable, logical components,
then test locally and run anywhere. With a unified view of pipelines and the assets they produce,
Dagster can schedule and orchestrate Pandas, Spark, SQL, or anything else that Python can invoke.

Dagster is designed for data platform engineers, data engineers, and full-stack data scientists.
Building a data platform with Dagster makes your stakeholders more independent and your systems
more robust. Developing data pipelines with Dagster makes testing easier and deploying faster.
""".strip()


def get_version():
    version = {}
    with open("dagster/version.py") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    return version["__version__"]


if __name__ == "__main__":
    setup(
        name="dagster",
        version=get_version(),
        author="Elementl",
        author_email="hello@elementl.com",
        license="Apache-2.0",
        description="A data orchestrator for machine learning, analytics, and ETL.",
        long_description=long_description(),
        long_description_content_type="text/markdown",
        url="https://github.com/dagster-io/dagster",
        classifiers=[
            "Programming Language :: Python :: 2.7",
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: OS Independent",
        ],
        packages=find_packages(exclude=["dagster_tests"]),
        package_data={
            "dagster": [
                "dagster/core/storage/event_log/sqlite/alembic/*",
                "dagster/core/storage/runs/sqlite/alembic/*",
                "dagster/core/storage/schedules/sqlite/alembic/*",
                "dagster/grpc/protos/*",
            ]
        },
        include_package_data=True,
        install_requires=[
            # standard python 2/3 compatability things
            'enum34; python_version < "3.4"',
            "future",
            "funcsigs",
            'functools32; python_version<"3"',
            "contextlib2>=0.5.4",
            'pathlib2>=2.3.4; python_version<"3"',
            # cli
            "click>=5.0",
            "coloredlogs>=6.1",
            "PyYAML",
            # core (not explicitly expressed atm)
            "alembic>=1.2.1",
            "croniter>=0.3.34",
            "grpcio>=1.32.0",  # ensure version we require is >= that with which we generated the grpc code (set in dev-requirements)
            "grpcio-health-checking>=1.32.0",
            "pendulum==1.4.4",  # pinned to match airflow, can upgrade to 2.0 once airflow 1.10.13 is released
            "protobuf>=3.13.0",  # ensure version we require is >= that with which we generated the proto code (set in dev-requirements)
            "pyrsistent>=0.14.8,<=0.16.0; python_version < '3'",  # 0.17.0 breaks py2 support
            "pyrsistent>=0.14.8; python_version >='3'",
            "python-dateutil",
            "requests",
            "rx<=1.6.1",  # 3.0 was a breaking change. No py2 compatability as well.
            'futures; python_version < "3"',
            "six",
            "tabulate",
            "tqdm",
            "sqlalchemy>=1.0",
            'typing; python_version<"3"',
            'backports.tempfile; python_version<"3"',
            "toposort>=1.0",
            "watchdog>=0.8.3",
            'psutil >= 1.0; platform_system=="Windows"',
            # https://github.com/mhammond/pywin32/issues/1439
            'pywin32 != 226; platform_system=="Windows"',
            "pytz",
            'docstring-parser==0.7.1; python_version >="3.6"',
        ],
        extras_require={"docker": ["docker"],},
        entry_points={
            "console_scripts": [
                "dagster = dagster.cli:main",
                "dagster-scheduler = dagster.scheduler.cli:main",
                "dagster-daemon = dagster.daemon.cli:main",
            ]
        },
    )

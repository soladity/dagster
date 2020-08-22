from setuptools import find_packages, setup


def get_version():
    version = {}
    with open("dagster_dask/version.py") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    return version["__version__"]


if __name__ == "__main__":
    setup(
        name="dagster-dask",
        version=get_version(),
        author="Elementl",
        author_email="hello@elementl.com",
        license="Apache-2.0",
        description="Package for using Dask as Dagster's execution engine.",
        url="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-dask",
        classifiers=[
            "Programming Language :: Python :: 2.7",
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: OS Independent",
        ],
        packages=find_packages(exclude=["test"]),
        install_requires=[
            "bokeh",
            "dagster",
            "dagster_graphql",
            "dask[dataframe]>=1.2.2",
            "distributed>=1.28.1",
        ],
        extras_require={
            "yarn": ["dask-yarn"],
            "pbs": ["dask-jobqueue"],
            "kube": ["dask-kubernetes"],
        },
        zip_safe=False,
    )

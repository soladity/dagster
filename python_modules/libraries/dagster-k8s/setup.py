from setuptools import find_packages, setup


def get_version():
    version = {}
    with open("dagster_k8s/version.py") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    return version["__version__"]


if __name__ == "__main__":
    setup(
        name="dagster-k8s",
        version=get_version(),
        author="Elementl",
        author_email="hello@elementl.com",
        license="Apache-2.0",
        description="A Dagster integration for k8s",
        url="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-k8s",
        classifiers=[
            "Programming Language :: Python :: 2.7",
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: OS Independent",
        ],
        packages=find_packages(exclude=["test"]),
        install_requires=[
            "dagster",
            "dagster_graphql",
            "kubernetes",
            # RSA 4.1+ is incompatible with py2.7
            'rsa<=4.0; python_version<"3"',
        ],
        tests_require=[],
        zip_safe=False,
    )

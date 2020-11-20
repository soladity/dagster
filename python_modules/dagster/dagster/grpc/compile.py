"""Compile the proto definitions into Python.

This tooling should be invoked to regenerate the Python grpc artifacts by running:

    python -m dagster.grpc.compile
"""
import os
import shutil
import subprocess
import sys

from dagster.utils import file_relative_path, safe_tempfile_path

PROTOS_DIR = file_relative_path(__file__, "protos")

PROTOS_PATH = os.path.join(PROTOS_DIR, "api.proto")

GENERATED_DIR = file_relative_path(__file__, "__generated__")

GENERATED_PB2_PATH = os.path.join(GENERATED_DIR, "api_pb2.py")

GENERATED_GRPC_PATH = os.path.join(GENERATED_DIR, "api_pb2_grpc.py")

ISORT_SETTINGS_PATH = file_relative_path(__file__, "../../../../")

GENERATED_HEADER = [
    ("# @" + "generated\n"),  # This is to avoid matching the phab rule
    "\n",
    "# This file was generated by running `python -m dagster.grpc.compile`\n",
    "# Do not edit this file directly, and do not attempt to recompile it using\n",
    "# grpc_tools.protoc directly, as several changes must be made to the raw output\n",
    "\n",
]

GENERATED_GRPC_PYLINT_DIRECTIVE = [
    "# pylint: disable=no-member, unused-argument\n",
    "\n",
]

GENERATED_PB2_PYLINT_DIRECTIVE = [
    "# pylint: disable=protected-access,no-name-in-module\n",
    "\n",
]


def protoc():
    # python -m grpc_tools.protoc \
    #   -I protos --python_out __generated__ --grpc_python_out __generated__ protos/api.proto
    _res = subprocess.check_output(
        [
            sys.executable,
            "-m",
            "grpc_tools.protoc",
            "-I",
            PROTOS_DIR,
            "--python_out",
            GENERATED_DIR,
            "--grpc_python_out",
            GENERATED_DIR,
            PROTOS_PATH,
        ]
    )

    # The generated api_pb2_grpc.py file must be altered in two ways:
    # 1. Add a pylint directive, `disable=no-member, unused-argument`
    # 2. Change the import from `import api_pb2 as api__pb2` to `from . import api_pb2 as api__pb2`.
    #    See: https://github.com/grpc/grpc/issues/22914
    with safe_tempfile_path() as tempfile_path:
        shutil.copyfile(
            GENERATED_GRPC_PATH, tempfile_path,
        )
        with open(tempfile_path, "r") as generated:
            with open(GENERATED_GRPC_PATH, "w") as rewritten:
                for line in GENERATED_HEADER:
                    rewritten.write(line)

                for line in GENERATED_GRPC_PYLINT_DIRECTIVE:
                    rewritten.write(line)

                for line in generated.readlines():
                    if line == "import api_pb2 as api__pb2\n":
                        rewritten.write("from . import api_pb2 as api__pb2\n")
                    else:
                        rewritten.write(line)

    with safe_tempfile_path() as tempfile_path:
        shutil.copyfile(
            GENERATED_PB2_PATH, tempfile_path,
        )
        with open(tempfile_path, "r") as generated:
            with open(GENERATED_PB2_PATH, "w") as rewritten:
                for line in GENERATED_HEADER:
                    rewritten.write(line)

                for line in GENERATED_PB2_PYLINT_DIRECTIVE:
                    rewritten.write(line)

                for line in generated.readlines():
                    rewritten.write(line)

    # We need to run black
    _res = subprocess.check_output(
        [
            sys.executable,
            "-m",
            "black",
            "-l",
            "100",
            "-t",
            "py35",
            "-t",
            "py36",
            "-t",
            "py37",
            "-t",
            "py38",
            GENERATED_DIR,
        ]
    )

    # And, finally, we need to run isort
    _res = subprocess.check_output(
        [
            "isort",
            "--settings-path",
            ISORT_SETTINGS_PATH,
            "-y",
            GENERATED_PB2_PATH,
            GENERATED_GRPC_PATH,
        ]
    )


if __name__ == "__main__":
    protoc()

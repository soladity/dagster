# pylint: disable=no-value-for-parameter

import json
import os
import shutil

import click
from dagster import file_relative_path


def read_json(filename):
    with open(filename) as f:
        data = json.load(f)
        return data


def write_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, sort_keys=True)


@click.command()
@click.option("--version", required=True, help="Version to release")
@click.option("--overwrite", is_flag=True, help="Overwrite an existing version")
def main(version, overwrite):
    content_directory = file_relative_path(__file__, "next/content")
    versioned_content_directory = file_relative_path(__file__, "next/.versioned_content")

    # Create version
    version_directory = os.path.join(versioned_content_directory, version)
    if os.path.isdir(version_directory):
        if not overwrite:
            raise click.ClickException(
                "Error: Version {} already exists. To overwrite this version, "
                "use the --overwrite option.".format(version)
            )

        value = click.prompt(
            "Are you sure you want to overwrite version {}? This is a dangerous action, make sure "
            "that the docs haven't drifted from the version that you are attempting to overwrite. "
            "It is okay if there is an error in old docs, it can be fixed in future releases.\n\n"
            "Enter the versld;fkjasion number to continue "
        )

        if value == version:
            shutil.rmtree(version_directory)
        else:
            raise click.ClickException("Incorrect version number: {}".format(value))

    shutil.copytree(content_directory, version_directory)

    # Overwite latest version
    latest_directory = os.path.join(versioned_content_directory, "latest")
    if os.path.isdir(latest_directory):
        shutil.rmtree(latest_directory)

    shutil.copytree(content_directory, latest_directory)

    # Create master navigation file
    versioned_navigation = {}
    for (root, _, files) in os.walk(versioned_content_directory):
        for filename in files:
            if filename == "_navigation.json":
                version = root.split("/")[-1]
                data = read_json(os.path.join(root, filename))
                versioned_navigation[version] = data

    write_json(
        os.path.join(versioned_content_directory, "_versioned_navigation.json"),
        versioned_navigation,
    )


if __name__ == "__main__":
    main()

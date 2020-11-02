import os
import subprocess
import sys

from dagster import check
from dagster.core.code_pointer import FileCodePointer
from dagster.core.definitions.reconstructable import (
    ReconstructablePipeline,
    ReconstructableRepository,
)
from dagster.core.host_representation import (
    ExternalPipeline,
    InProcessRepositoryLocationOrigin,
    RepositoryLocation,
    RepositoryLocationHandle,
)
from dagster.core.origin import PipelinePythonOrigin, RepositoryPythonOrigin
from dagster.serdes import whitelist_for_serdes
from dagster.utils import file_relative_path, git_repository_root

IS_BUILDKITE = os.getenv("BUILDKITE") is not None


def test_repo_path():
    return os.path.join(
        git_repository_root(), "python_modules", "dagster-test", "dagster_test", "test_project"
    )


def test_project_environments_path():
    return os.path.join(test_repo_path(), "environments")


def build_and_tag_test_image(tag):
    check.str_param(tag, "tag")

    base_python = "3.7.8"

    # Build and tag local dagster test image
    return subprocess.check_output(["./build.sh", base_python, tag], cwd=test_repo_path())


def get_test_project_recon_pipeline(pipeline_name):
    return ReOriginatedReconstructablePipelineForTest(
        ReconstructableRepository.for_file(
            file_relative_path(__file__, "test_pipelines/repo.py"), "define_demo_execution_repo",
        ).get_reconstructable_pipeline(pipeline_name)
    )


class ReOriginatedReconstructablePipelineForTest(ReconstructablePipeline):
    def __new__(  # pylint: disable=signature-differs
        cls, reconstructable_pipeline,
    ):
        return super(ReOriginatedReconstructablePipelineForTest, cls).__new__(
            cls,
            reconstructable_pipeline.repository,
            reconstructable_pipeline.pipeline_name,
            reconstructable_pipeline.solid_selection_str,
            reconstructable_pipeline.solids_to_execute,
        )

    def get_origin(self):
        """
        Hack! Inject origin that the docker-celery images will use. The BK image uses a different
        directory structure (/workdir/python_modules/dagster-test/dagster_test/test_project) than
        the test that creates the ReconstructablePipeline. As a result the normal origin won't
        work, we need to inject this one.
        """

        return PipelinePythonOrigin(
            self.pipeline_name,
            RepositoryPythonOrigin(
                executable_path="python",
                code_pointer=FileCodePointer(
                    "/dagster_test/test_project/test_pipelines/repo.py",
                    "define_demo_execution_repo",
                ),
            ),
        )


class ReOriginatedExternalPipelineForTest(ExternalPipeline):
    def __init__(
        self, external_pipeline,
    ):
        super(ReOriginatedExternalPipelineForTest, self).__init__(
            external_pipeline.external_pipeline_data, external_pipeline.repository_handle,
        )

    def get_origin(self):
        """
        Hack! Inject origin that the k8s images will use. The BK image uses a different directory
        structure (/workdir/python_modules/dagster-test/dagster_test/test_project) than the images
        inside the kind cluster (/dagster_test/test_project). As a result the normal origin won't
        work, we need to inject this one.
        """

        return PipelinePythonOrigin(
            self._pipeline_index.name,
            RepositoryPythonOrigin(
                executable_path="python",
                code_pointer=FileCodePointer(
                    "/dagster_test/test_project/test_pipelines/repo.py",
                    "define_demo_execution_repo",
                ),
            ),
        )


def get_test_project_external_pipeline(pipeline_name):
    return (
        RepositoryLocation.from_handle(
            RepositoryLocationHandle.create_from_repository_location_origin(
                InProcessRepositoryLocationOrigin(
                    ReconstructableRepository.for_file(
                        file_relative_path(__file__, "test_pipelines/repo.py"),
                        "define_demo_execution_repo",
                    )
                )
            )
        )
        .get_repository("demo_execution_repo")
        .get_full_external_pipeline(pipeline_name)
    )


def test_project_docker_image():
    docker_repository = os.getenv("DAGSTER_DOCKER_REPOSITORY")
    image_name = os.getenv("DAGSTER_DOCKER_IMAGE", "dagster-docker-buildkite")
    docker_image_tag = os.getenv("DAGSTER_DOCKER_IMAGE_TAG")

    if IS_BUILDKITE:
        assert docker_image_tag is not None, (
            "This test requires the environment variable DAGSTER_DOCKER_IMAGE_TAG to be set "
            "to proceed"
        )
        assert docker_repository is not None, (
            "This test requires the environment variable DAGSTER_DOCKER_REPOSITORY to be set "
            "to proceed"
        )

    # This needs to be a domain name to avoid the k8s machinery automatically prefixing it with
    # `docker.io/` and attempting to pull images from Docker Hub
    if not docker_repository:
        docker_repository = "dagster.io.priv"

    if not docker_image_tag:
        # Detect the python version we're running on
        majmin = str(sys.version_info.major) + str(sys.version_info.minor)

        docker_image_tag = "py{majmin}-{image_version}".format(
            majmin=majmin, image_version="latest"
        )

    final_docker_image = "{repository}/{image_name}:{tag}".format(
        repository=docker_repository, image_name=image_name, tag=docker_image_tag
    )
    print("Using Docker image: %s" % final_docker_image)  # pylint: disable=print-call
    return final_docker_image

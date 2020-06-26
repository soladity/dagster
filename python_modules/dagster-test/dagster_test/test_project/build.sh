#!/bin/bash

ROOT=$(git rev-parse --show-toplevel)
BASE_DIR="${ROOT}/python_modules/dagster-test/dagster_test/test_project"

function cleanup {
    rm -rf "${BASE_DIR}/build_cache"
    set +ux
}

# ensure cleanup happens on error or normal exit
trap cleanup INT TERM EXIT ERR


if [ "$#" -ne 2 ]; then
    echo "Error: Must specify a Python version and image tag.\n" 1>&2
    echo "Usage: ./build.sh 3.7.4 dagster-test-image" 1>&2
    exit 1
fi
set -ux

# e.g. 3.7.4
PYTHON_VERSION=$1

# e.g. dagster-test-image
IMAGE_TAG=$2

pushd $BASE_DIR

mkdir -p build_cache

cp $GOOGLE_APPLICATION_CREDENTIALS ./build_cache/gac.json

echo -e "--- \033[32m:truck: Copying files...\033[0m"
cp -R $ROOT/python_modules/dagster \
      $ROOT/python_modules/dagit \
      $ROOT/python_modules/dagster-graphql \
      $ROOT/python_modules/libraries/dagster-airflow \
      $ROOT/python_modules/libraries/dagster-aws \
      $ROOT/python_modules/libraries/dagster-celery \
      $ROOT/python_modules/libraries/dagster-celery-k8s \
      $ROOT/python_modules/libraries/dagster-cron \
      $ROOT/python_modules/libraries/dagster-pandas \
      $ROOT/python_modules/libraries/dagster-postgres \
      $ROOT/python_modules/libraries/dagster-gcp \
      $ROOT/python_modules/libraries/dagster-k8s \
      $ROOT/examples \
      build_cache/

find . \( -name '*.egg-info' -o -name '*.tox' -o -name 'dist' \) | xargs rm -rf

echo -e "--- \033[32m:docker: Building Docker image\033[0m"
docker build . \
    --no-cache \
    --build-arg PYTHON_VERSION="${PYTHON_VERSION}" \
    -t "${IMAGE_TAG}"

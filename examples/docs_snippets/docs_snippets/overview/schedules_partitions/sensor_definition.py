import os

from dagster.core.definitions.decorators.sensor import sensor
from dagster.core.definitions.job import RunRequest

MY_DIRECTORY = "/my/test/directory"

# start_sensor_marker_0
@sensor(pipeline_name="log_file_pipeline")
def my_directory_sensor(_context):
    for filename in os.listdir(MY_DIRECTORY):
        filepath = os.path.join(MY_DIRECTORY, filename)
        if os.path.isfile(filepath):
            yield RunRequest(
                run_key=filename,
                run_config={"solids": {"process_file": {"config": {"filename": filename}}}},
            )


# end_sensor_marker_0

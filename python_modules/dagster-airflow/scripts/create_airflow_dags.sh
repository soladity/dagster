#!/bin/bash

set -ex

dagster-airflow scaffold --dag-name toys_log_spew    --module-name toys.log_spew    --fn-name define_spew_pipeline
dagster-airflow scaffold --dag-name toys_many_events --module-name toys.many_events --fn-name define_many_events_pipeline
dagster-airflow scaffold --dag-name toys_resources   --module-name toys.resources   --fn-name define_resource_pipeline
dagster-airflow scaffold --dag-name toys_sleepy      --module-name toys.sleepy      --fn-name define_sleepy_pipeline

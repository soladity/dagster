from dagster import repository

from .ge_demo import payroll_data


@repository
def ge_example_repo():
    return [payroll_data]

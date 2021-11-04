# start_repo_marker_0
from airflow_ingest.airflow_complex_dag import complex_dag
from airflow_ingest.airflow_simple_dag import simple_dag
from dagster import repository
from dagster_airflow.dagster_job_factory import make_dagster_job_from_airflow_dag

airflow_simple_dag = make_dagster_job_from_airflow_dag(simple_dag)
airflow_complex_dag = make_dagster_job_from_airflow_dag(complex_dag)


@repository
def airflow_ingest_example():
    return [airflow_complex_dag, airflow_simple_dag]


# end_repo_marker_0


# start_repo_marker_1

airflow_simple_dag_with_execution_date = make_dagster_job_from_airflow_dag(
    dag=simple_dag, tags={"airflow_execution_date": "2021-11-01 00:00:00"}
)
# end_repo_marker_1

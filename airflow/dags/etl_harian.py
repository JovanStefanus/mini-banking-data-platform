"""DAG harian: pipeline ETL dari core banking, MySQL, dan MongoDB ke data warehouse.

Alur: cek koneksi -> jalankan pipeline -> ringkas hasil audit.
Kode ETL tidak diubah; Airflow hanya menjadwalkan, mengulang kalau gagal, dan menampilkan statusnya.
"""
from datetime import timedelta

import pendulum
from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG

default_args = {
    "owner": "data-engineering",
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="core_to_dwh_daily",
    description="ETL harian: PostgreSQL + MySQL + MongoDB -> data warehouse",
    schedule="0 1 * * *",                                   # setiap hari 01:00 WIB
    start_date=pendulum.datetime(2026, 1, 1, tz="Asia/Jakarta"),
    catchup=False,
    max_active_runs=1,
    default_args=default_args,
    tags=["etl", "dwh"],
) as dag:

    cek_koneksi = BashOperator(
        task_id="cek_koneksi",
        bash_command="cd /opt/airflow/project && python -m etl.healthcheck",
        execution_timeout=timedelta(minutes=2),
    )

    jalankan_etl = BashOperator(
        task_id="jalankan_pipeline_etl",
        bash_command="cd /opt/airflow/project && python -m etl.run_pipeline",
        execution_timeout=timedelta(minutes=30),
    )

    ringkas_audit = BashOperator(
        task_id="ringkas_audit",
        bash_command="cd /opt/airflow/project && python -m etl.audit_report",
        execution_timeout=timedelta(minutes=2),
    )

    cek_koneksi >> jalankan_etl >> ringkas_audit

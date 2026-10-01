"""Pemeriksaan DAG Airflow tanpa menginstal Airflow: file dibaca sebagai teks/AST."""
import ast
import re
from pathlib import Path

DAG_FILE = Path(__file__).resolve().parent.parent / "airflow" / "dags" / "etl_harian.py"
SUMBER = DAG_FILE.read_text(encoding="utf-8")


def _argumen_dag():
    for node in ast.walk(ast.parse(SUMBER)):
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "DAG":
            return {kw.arg: kw.value for kw in node.keywords}
    raise AssertionError("pemanggilan DAG(...) tidak ditemukan")


def test_dag_id_sama_dengan_nama_pipeline_di_audit_log():
    assert ast.literal_eval(_argumen_dag()["dag_id"]) == "core_to_dwh_daily"


def test_jadwal_harian_dan_tanpa_catchup():
    argumen = _argumen_dag()
    assert ast.literal_eval(argumen["schedule"]) == "0 1 * * *"
    assert ast.literal_eval(argumen["catchup"]) is False


def test_hanya_satu_run_aktif_dalam_satu_waktu():
    assert ast.literal_eval(_argumen_dag()["max_active_runs"]) == 1


def test_retry_diaktifkan():
    cocok = re.search(r'"retries":\s*(\d+)', SUMBER)
    assert cocok and int(cocok.group(1)) >= 1


def test_task_menjalankan_pipeline_etl():
    assert "python -m etl.run_pipeline" in SUMBER


def test_urutan_task_cek_koneksi_etl_audit():
    assert re.search(r"cek_koneksi\s*>>\s*jalankan_etl\s*>>\s*ringkas_audit", SUMBER)

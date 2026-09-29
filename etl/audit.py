"""Pencatatan setiap langkah pipeline ke audit.etl_audit_log.
Memakai koneksi autocommit terpisah supaya log FAILED tetap tersimpan
walaupun transaksi ETL di-rollback."""


def start_run(conn, pipeline, target):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO audit.etl_audit_log(pipeline_name, target_table, status) "
            "VALUES (%s, %s, 'RUNNING') RETURNING run_id", (pipeline, target))
        return cur.fetchone()[0]


def finish_run(conn, run_id, status, rows_read=None, rows_loaded=None, rows_rejected=None, error=None):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE audit.etl_audit_log SET status=%s, rows_read=%s, rows_loaded=%s, "
            "rows_rejected=%s, error_message=%s, finished_at=now() WHERE run_id=%s",
            (status, rows_read, rows_loaded, rows_rejected, error, run_id))


def log_dq(conn, run_id, check_name, passed, detail):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO audit.dq_check_result(run_id, check_name, passed, detail) VALUES (%s,%s,%s,%s)",
            (run_id, check_name, passed, detail))

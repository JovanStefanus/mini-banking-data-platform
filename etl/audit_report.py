"""Ringkasan run pipeline terakhir dari audit.etl_audit_log.

Dipakai sebagai task monitoring di Airflow, dan bisa dijalankan manual:  python -m etl.audit_report
Run terakhir = semua langkah sejak langkah pertama (staging.cabang) pada run terbaru.
"""
import sys

from .config import dwh_conn

QUERY = """
    SELECT target_table, status, rows_read, rows_loaded, rows_rejected,
           ROUND(EXTRACT(EPOCH FROM (finished_at - started_at))::numeric, 1) AS detik
      FROM audit.etl_audit_log
     WHERE run_id >= (SELECT COALESCE(MAX(run_id), 0) FROM audit.etl_audit_log
                       WHERE target_table = 'staging.cabang')
     ORDER BY run_id
"""


def main():
    conn = dwh_conn()
    try:
        cur = conn.cursor()
        cur.execute(QUERY)
        baris = cur.fetchall()
    finally:
        conn.close()

    if not baris:
        print("Belum ada catatan pipeline di audit.etl_audit_log")
        return 1

    print(f"{'langkah':<26}{'status':<10}{'dibaca':>8}{'dimuat':>8}{'ditolak':>8}{'detik':>8}")
    for target, status, dibaca, dimuat, ditolak, detik in baris:
        print(f"{target:<26}{status:<10}{str(dibaca or '-'):>8}{str(dimuat or '-'):>8}"
              f"{str(ditolak or '-'):>8}{str(detik or '-'):>8}")

    gagal = [target for target, status, *_ in baris if status == "FAILED"]
    if gagal:
        print(f"\nLangkah gagal: {', '.join(gagal)}")
        return 1
    print(f"\n{len(baris)} langkah tercatat, tidak ada yang gagal.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

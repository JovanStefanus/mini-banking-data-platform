"""Cek koneksi ke semua sumber dan DWH.

Dipakai sebagai task pertama di Airflow, supaya kegagalan koneksi terlihat jelas
sebelum pipeline berjalan. Bisa juga dijalankan manual:  python -m etl.healthcheck
"""
import sys

from .config import dwh_conn, mongo_client, mysql_conn, source_conn


def _cek_sql(buka):
    conn = buka()
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
    finally:
        conn.close()


def _cek_mongo(buka):
    client = buka()
    try:
        client.admin.command("ping")
    finally:
        client.close()


def main():
    pemeriksaan = [
        ("postgres_core", _cek_sql, source_conn),
        ("postgres_dwh", _cek_sql, dwh_conn),
        ("mysql_channel", _cek_sql, mysql_conn),
        ("mongo_logs", _cek_mongo, mongo_client),
    ]
    semua_sehat = True
    for nama, cek, buka in pemeriksaan:
        try:
            cek(buka)
            print(f"[OK]     {nama}")
        except Exception as exc:          # noqa: BLE001 - semua jenis error harus dilaporkan
            semua_sehat = False
            print(f"[GAGAL]  {nama}: {exc}")
    return 0 if semua_sehat else 1


if __name__ == "__main__":
    sys.exit(main())

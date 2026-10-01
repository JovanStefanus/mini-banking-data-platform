"""Pipeline ETL: core banking (PostgreSQL) + channel (MySQL) + log (MongoDB) -> staging -> star schema DWH.

Jalankan dari root repo (venv aktif, .env sudah dimuat):
    python -m etl.run_pipeline
"""
import sys
import time
from pathlib import Path

from . import audit, data_quality, data_quality_channel, load_channel as lc, transform_load as tl
from .config import dwh_conn, mongo_client, mysql_conn, source_conn
from .extract import extract, fact_watermark
from .extract_channel import extract_mongo_log, extract_mysql

PIPELINE = "core_to_dwh_daily"
ROOT = Path(__file__).resolve().parent.parent


def scalar(dwh, sql):
    cur = dwh.cursor()
    cur.execute(sql)
    return cur.fetchone()[0]


def run_step(audit_conn, dwh, target, fn):
    run_id = audit.start_run(audit_conn, PIPELINE, target)
    t0 = time.time()
    try:
        read, loaded, rejected = fn()
        dwh.commit()
        audit.finish_run(audit_conn, run_id, "SUCCESS", read, loaded, rejected)
        print(f"[OK]     {target:<26} read={read:<7} loaded={loaded:<7} rejected={rejected:<5} ({time.time() - t0:.1f}s)")
    except Exception as exc:
        dwh.rollback()
        audit.finish_run(audit_conn, run_id, "FAILED", error=str(exc))
        print(f"[FAILED] {target}: {exc}")
        raise


def main():
    src, dwh, audit_conn = source_conn(), dwh_conn(), dwh_conn(autocommit=True)
    my, mongo = mysql_conn(), mongo_client()
    try:
        dwh.cursor().execute((Path(__file__).parent / "sql" / "staging.sql").read_text())
        dwh.cursor().execute((ROOT / "sql" / "dwh" / "02_channel_tables.sql").read_text())
        dwh.commit()

        wm = fact_watermark(dwh)
        wm_sesi = scalar(dwh, "SELECT COALESCE(MAX(id_sesi), 0) FROM dwh.fact_sesi_login")
        wm_log = scalar(dwh, "SELECT COALESCE(MAX(id_log), '') FROM dwh.fact_aktivitas") or None
        print(f"Watermark: transaksi > {wm} | sesi_login > {wm_sesi} | log_aktivitas > {wm_log or '(awal)'}\n")

        steps = [
            ("staging.cabang",   lambda: extract(src, dwh, "cabang", ["kode_cabang", "nama_cabang", "kota"])),
            ("staging.produk",   lambda: extract(src, dwh, "produk", ["kode_produk", "nama_produk", "jenis"])),
            ("staging.nasabah",  lambda: extract(src, dwh, "nasabah",
                                                 ["id_nasabah", "nama", "kota", "segmen", "tgl_daftar", "updated_at"])),
            ("staging.rekening", lambda: extract(src, dwh, "rekening",
                                                 ["no_rekening", "id_nasabah", "kode_produk", "kode_cabang"])),
            ("staging.transaksi", lambda: extract(src, dwh, "transaksi",
                                                  ["id_transaksi", "no_rekening", "jenis_transaksi", "nominal",
                                                   "channel", "waktu_transaksi"],
                                                  where="id_transaksi > %s", params=(wm,), order_by="id_transaksi")),
            ("dwh.dim_waktu",    lambda: tl.load_dim_waktu(dwh)),
            ("dwh.dim_cabang",   lambda: tl.load_dim_cabang(dwh)),
            ("dwh.dim_produk",   lambda: tl.load_dim_produk(dwh)),
            ("dwh.dim_nasabah",  lambda: tl.load_dim_nasabah_scd2(dwh)),
            ("dwh.fact_transaksi", lambda: tl.load_fact_transaksi(dwh)),
            # --- sumber channel (MySQL) dan log (MongoDB) ---
            ("staging.mobile_user", lambda: extract_mysql(
                my, dwh, "mobile_user", ["id_user", "id_nasabah", "device_type", "tgl_aktivasi", "status"])),
            ("staging.sesi_login", lambda: extract_mysql(
                my, dwh, "sesi_login", ["id_sesi", "id_user", "waktu_login", "durasi_detik", "berhasil"],
                where="id_sesi > %s", params=(wm_sesi,), order_by="id_sesi")),
            ("staging.log_aktivitas", lambda: extract_mongo_log(mongo, dwh, wm_log)),
            ("dwh.dim_mobile_user",  lambda: lc.load_dim_mobile_user(dwh)),
            ("dwh.fact_sesi_login",  lambda: lc.load_fact_sesi_login(dwh)),
            ("dwh.fact_aktivitas",   lambda: lc.load_fact_aktivitas(dwh)),
        ]
        for target, fn in steps:
            run_step(audit_conn, dwh, target, fn)

        print("\nData quality check:")
        dq_run = audit.start_run(audit_conn, PIPELINE, "data_quality")
        failed = data_quality.run_checks(src, dwh, audit_conn, dq_run)
        failed += data_quality_channel.run_checks_channel(my, mongo, dwh, audit_conn, dq_run)
        if failed:
            audit.finish_run(audit_conn, dq_run, "FAILED", error="; ".join(failed))
            print(f"\nPipeline SELESAI dengan {len(failed)} check gagal.")
            sys.exit(1)
        audit.finish_run(audit_conn, dq_run, "SUCCESS")
        print("\nPipeline selesai. Semua check lulus.")
    finally:
        for c in (src, dwh, audit_conn, my, mongo):
            c.close()


if __name__ == "__main__":
    main()

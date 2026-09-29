"""Pipeline ETL: core banking -> staging -> star schema DWH.

Jalankan dari root repo (venv aktif, .env sudah dimuat):
    python -m etl.run_pipeline
"""
import sys
import time
from pathlib import Path

from . import audit, data_quality, transform_load as tl
from .config import dwh_conn, source_conn
from .extract import extract, fact_watermark

PIPELINE = "core_to_dwh_daily"


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
    try:
        dwh.cursor().execute((Path(__file__).parent / "sql" / "staging.sql").read_text())
        dwh.commit()

        wm = fact_watermark(dwh)
        print(f"Watermark fact_transaksi: id_transaksi > {wm}\n")

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
        ]
        for target, fn in steps:
            run_step(audit_conn, dwh, target, fn)

        print("\nData quality check:")
        dq_run = audit.start_run(audit_conn, PIPELINE, "data_quality")
        failed = data_quality.run_checks(src, dwh, audit_conn, dq_run)
        if failed:
            audit.finish_run(audit_conn, dq_run, "FAILED", error="; ".join(failed))
            print(f"\nPipeline SELESAI dengan {len(failed)} check gagal.")
            sys.exit(1)
        audit.finish_run(audit_conn, dq_run, "SUCCESS")
        print("\nPipeline selesai. Semua check lulus.")
    finally:
        for c in (src, dwh, audit_conn):
            c.close()


if __name__ == "__main__":
    main()

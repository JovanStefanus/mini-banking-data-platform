"""Data quality check untuk data channel dan log. Hasil dicatat ke audit.dq_check_result."""
from bson import ObjectId

from . import audit


def run_checks_channel(my, mongo, dwh, audit_conn, run_id):
    dcur = dwh.cursor()
    results = []

    def zero_check(name, sql):
        dcur.execute(sql)
        n = dcur.fetchone()[0]
        results.append((name, n == 0, f"{n} baris bermasalah"))

    zero_check("fact_sesi_login: durasi tidak negatif",
               "SELECT COUNT(*) FROM dwh.fact_sesi_login WHERE durasi_detik < 0")
    zero_check("dim_mobile_user: id_nasabah ada di dim_nasabah",
               "SELECT COUNT(*) FROM dwh.dim_mobile_user m WHERE NOT EXISTS "
               "(SELECT 1 FROM dwh.dim_nasabah n WHERE n.id_nasabah = m.id_nasabah)")
    zero_check("fact_aktivitas: id_nasabah ada di dim_nasabah",
               "SELECT COUNT(*) FROM dwh.fact_aktivitas a WHERE NOT EXISTS "
               "(SELECT 1 FROM dwh.dim_nasabah n WHERE n.id_nasabah = a.id_nasabah)")

    # Rekonsiliasi jumlah baris terhadap sumber (sampai watermark yang sudah dimuat)
    dcur.execute("SELECT COALESCE(MAX(id_sesi), 0), COUNT(*) FROM dwh.fact_sesi_login")
    max_sesi, f_sesi = dcur.fetchone()
    if max_sesi:
        mcur = my.cursor()
        mcur.execute("SELECT COUNT(*) FROM sesi_login WHERE id_sesi <= %s", (max_sesi,))
        s_sesi = mcur.fetchone()[0]
        mcur.close()
        results.append(("rekonsiliasi sesi_login MySQL vs fact", s_sesi == f_sesi,
                        f"sumber={s_sesi} fact={f_sesi}"))

    dcur.execute("SELECT MAX(id_log), COUNT(*) FROM dwh.fact_aktivitas")
    max_log, f_log = dcur.fetchone()
    if max_log:
        s_log = mongo["banking_logs"]["log_aktivitas"].count_documents({"_id": {"$lte": ObjectId(max_log)}})
        results.append(("rekonsiliasi log_aktivitas MongoDB vs fact", s_log == f_log,
                        f"sumber={s_log} fact={f_log}"))

    failed = []
    for name, passed, detail in results:
        audit.log_dq(audit_conn, run_id, name, passed, detail)
        print(f"      [{'PASS' if passed else 'FAIL'}] {name} ({detail})")
        if not passed:
            failed.append(name)
    return failed

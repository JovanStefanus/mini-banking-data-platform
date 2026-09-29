"""Data quality check setelah load. Hasil dicatat ke audit.dq_check_result."""
from . import audit


def run_checks(src, dwh, audit_conn, run_id):
    dcur, scur = dwh.cursor(), src.cursor()
    results = []

    def zero_check(name, sql):
        dcur.execute(sql)
        n = dcur.fetchone()[0]
        results.append((name, n == 0, f"{n} baris bermasalah"))

    zero_check("dim_nasabah: business key/nama tidak NULL",
               "SELECT COUNT(*) FROM dwh.dim_nasabah WHERE id_nasabah IS NULL OR nama IS NULL")
    zero_check("dim_nasabah: tepat 1 versi current per nasabah",
               "SELECT COUNT(*) FROM (SELECT id_nasabah FROM dwh.dim_nasabah "
               "GROUP BY id_nasabah HAVING SUM(is_current::int) <> 1) x")
    zero_check("fact_transaksi: nominal harus > 0",
               "SELECT COUNT(*) FROM dwh.fact_transaksi WHERE nominal <= 0")

    # Rekonsiliasi jumlah baris dan total nominal terhadap sumber
    dcur.execute("SELECT MAX(id_transaksi), COUNT(*), COALESCE(SUM(nominal),0) FROM dwh.fact_transaksi")
    max_id, f_cnt, f_sum = dcur.fetchone()
    if max_id is not None:
        scur.execute("SELECT COUNT(*), COALESCE(SUM(nominal),0) FROM transaksi WHERE id_transaksi <= %s", (max_id,))
        s_cnt, s_sum = scur.fetchone()
        results.append(("rekonsiliasi jumlah baris sumber vs fact", s_cnt == f_cnt, f"sumber={s_cnt} fact={f_cnt}"))
        results.append(("rekonsiliasi total nominal sumber vs fact", s_sum == f_sum, f"sumber={s_sum} fact={f_sum}"))

    failed = []
    for name, passed, detail in results:
        audit.log_dq(audit_conn, run_id, name, passed, detail)
        print(f"      [{'PASS' if passed else 'FAIL'}] {name} ({detail})")
        if not passed:
            failed.append(name)
    return failed

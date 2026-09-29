"""EXTRACT: salin data dari sumber ke schema staging di DWH."""
from psycopg2.extras import execute_values


def extract(src, dwh, table, cols, where="", params=(), order_by="", batch=10000):
    """Reload staging.<table> dari tabel sumber dengan nama sama.
    Memakai server-side cursor supaya memori tetap kecil untuk data besar."""
    col_list = ", ".join(cols)
    sql = f"SELECT {col_list} FROM {table}"
    if where:
        sql += f" WHERE {where}"
    if order_by:
        sql += f" ORDER BY {order_by}"

    dwh_cur = dwh.cursor()
    dwh_cur.execute(f"TRUNCATE staging.{table}")

    src_cur = src.cursor(name=f"cur_{table}")
    src_cur.itersize = batch
    src_cur.execute(sql, params)
    total = 0
    while True:
        rows = src_cur.fetchmany(batch)
        if not rows:
            break
        execute_values(dwh_cur, f"INSERT INTO staging.{table} ({col_list}) VALUES %s", rows, page_size=batch)
        total += len(rows)
    src_cur.close()
    return total, total, 0   # read, loaded, rejected


def fact_watermark(dwh):
    """Id transaksi terbesar yang sudah masuk fact. Dipakai untuk incremental load."""
    cur = dwh.cursor()
    cur.execute("SELECT COALESCE(MAX(id_transaksi), 0) FROM dwh.fact_transaksi")
    return cur.fetchone()[0]

"""EXTRACT untuk sumber channel: MySQL (mobile banking) dan MongoDB (log aktivitas)."""
from bson import ObjectId
from psycopg2.extras import execute_values


def extract_mysql(my, dwh, table, cols, where="", params=(), order_by="", batch=5000):
    """Reload staging.<table> dari tabel MySQL dengan nama sama."""
    col_list = ", ".join(cols)
    sql = f"SELECT {col_list} FROM {table}"
    if where:
        sql += f" WHERE {where}"
    if order_by:
        sql += f" ORDER BY {order_by}"

    dcur = dwh.cursor()
    dcur.execute(f"TRUNCATE staging.{table}")
    mcur = my.cursor()
    mcur.execute(sql, params)
    total = 0
    while True:
        rows = mcur.fetchmany(batch)
        if not rows:
            break
        execute_values(dcur, f"INSERT INTO staging.{table} ({col_list}) VALUES %s", rows, page_size=batch)
        total += len(rows)
    mcur.close()
    return total, total, 0   # read, loaded, rejected


def extract_mongo_log(mongo, dwh, last_id=None, batch=5000):
    """Ambil log aktivitas yang _id-nya lebih besar dari watermark (incremental).
    Dokumen yang tidak lengkap ditolak dan dihitung sebagai rejected.
    Alamat IP sengaja tidak diambil (data minimization)."""
    col = mongo["banking_logs"]["log_aktivitas"]
    query = {"_id": {"$gt": ObjectId(last_id)}} if last_id else {}
    sql = ("INSERT INTO staging.log_aktivitas "
           "(id_log, id_nasabah, aksi, os, versi_app, waktu_aktivitas, sukses) VALUES %s")

    dcur = dwh.cursor()
    dcur.execute("TRUNCATE staging.log_aktivitas")
    buf, read, rejected = [], 0, 0

    def flush():
        if buf:
            execute_values(dcur, sql, buf, page_size=batch)
            buf.clear()

    for doc in col.find(query).sort("_id", 1).batch_size(batch):
        read += 1
        if doc.get("id_nasabah") is None or doc.get("waktu") is None or not doc.get("aksi"):
            rejected += 1
            continue
        perangkat = doc.get("perangkat") or {}
        buf.append((str(doc["_id"]), doc["id_nasabah"], doc["aksi"], perangkat.get("os"),
                    perangkat.get("versi_app"), doc["waktu"], bool(doc.get("sukses"))))
        if len(buf) >= batch:
            flush()
    flush()
    return read, read - rejected, rejected

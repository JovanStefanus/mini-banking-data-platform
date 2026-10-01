"""Simulasi aktivitas baru di MySQL dan MongoDB untuk menguji incremental load.
Jalankan SEBELUM menjalankan pipeline berikutnya.

    python -m etl.simulate_channel
"""
import random
from datetime import datetime, timedelta

import mysql.connector
from pymongo import MongoClient

from .config import _env


def main():
    now = datetime.now()   # waktu lokal naive, sama dengan generator

    conn = mysql.connector.connect(
        host=_env("MYSQL_HOST", "127.0.0.1"), port=int(_env("MYSQL_PORT", "3307")),
        database="channel_banking", user="channel_user", password=_env("MYSQL_PASSWORD", ""))
    cur = conn.cursor()
    cur.execute("SELECT id_user, id_nasabah FROM mobile_user")
    users = cur.fetchall()
    rows = [(random.choice(users)[0], now - timedelta(minutes=random.randint(0, 60)),
             random.randint(20, 900), 1) for _ in range(100)]
    cur.executemany("INSERT INTO sesi_login(id_user, waktu_login, durasi_detik, berhasil) VALUES (%s,%s,%s,%s)", rows)
    conn.commit()
    conn.close()
    print(f"[mysql] {len(rows)} sesi_login baru")

    client = MongoClient(host=_env("MONGO_HOST", "127.0.0.1"), port=int(_env("MONGO_PORT", "27017")),
                         username="mongo_user", password=_env("MONGO_PASSWORD", ""), authSource="admin")
    aksi = ["LOGIN", "CEK_SALDO", "TRANSFER", "BAYAR_TAGIHAN", "LOGOUT"]
    docs = [{"id_nasabah": random.choice(users)[1], "aksi": random.choice(aksi),
             "perangkat": {"os": random.choice(["ANDROID", "IOS"]), "versi_app": "9.1"},
             "waktu": now - timedelta(minutes=random.randint(0, 60)), "sukses": True} for _ in range(100)]
    client["banking_logs"]["log_aktivitas"].insert_many(docs)
    client.close()
    print(f"[mongo] {len(docs)} log_aktivitas baru")


if __name__ == "__main__":
    main()

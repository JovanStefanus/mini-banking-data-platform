"""Generator data sintetis untuk Mini Banking Data Platform.
Semua data palsu (Faker). Aman dijalankan berulang: tabel di-TRUNCATE dulu.

Contoh:
    python generate.py --nasabah 5000 --transaksi 200000
"""
import argparse
import os
import random
from datetime import datetime, timedelta

import mysql.connector
import psycopg2
from faker import Faker
from psycopg2.extras import execute_values
from pymongo import MongoClient

fake = Faker("id_ID")
Faker.seed(42)
random.seed(42)

CABANG = [
    ("C001", "KCU Jakarta Sudirman", "Jakarta"), ("C002", "KCP Bandung Braga", "Bandung"),
    ("C003", "KCU Surabaya Tunjungan", "Surabaya"), ("C004", "KCP Medan Kesawan", "Medan"),
    ("C005", "KCU Semarang Pemuda", "Semarang"), ("C006", "KCP Yogyakarta Malioboro", "Yogyakarta"),
    ("C007", "KCU Makassar Losari", "Makassar"), ("C008", "KCP Denpasar Sanur", "Denpasar"),
]
PRODUK = [
    ("P001", "Tabungan Reguler", "TABUNGAN"), ("P002", "Tabungan Prioritas", "TABUNGAN"),
    ("P003", "Giro Bisnis", "GIRO"), ("P004", "Deposito Berjangka", "DEPOSITO"),
    ("P005", "Kredit Multiguna", "KREDIT"),
]
JENIS_TRX = ["SETOR", "TARIK", "TRANSFER_KELUAR", "TRANSFER_MASUK", "BAYAR"]
CHANNEL = ["ATM", "MOBILE", "INTERNET", "TELLER"]
SEGMEN = ["RITEL", "PRIORITAS", "BISNIS"]


def env(key, default):
    return os.environ.get(key, default)


def masked_nik():
    return f"{random.choice(['3273','3171','3578','1271'])}********{random.randint(1, 9999):04d}"


def gen_pg(n_nasabah, n_trx):
    conn = psycopg2.connect(
        host=env("PG_CORE_HOST", "localhost"), port=env("PG_CORE_PORT", "5432"),
        dbname="core_banking", user="core_user", password=env("PG_CORE_PASSWORD", "change_me_core"))
    cur = conn.cursor()
    cur.execute("TRUNCATE transaksi, rekening, nasabah, produk, cabang RESTART IDENTITY CASCADE")

    execute_values(cur, "INSERT INTO cabang VALUES %s", CABANG)
    execute_values(cur, "INSERT INTO produk VALUES %s", PRODUK)

    today = datetime.now()
    nasabah_rows = []
    for _ in range(n_nasabah):
        daftar = today - timedelta(days=random.randint(120, 1500))
        nasabah_rows.append((masked_nik(), fake.name(), fake.email(), random.choice(CABANG)[2],
                             random.choices(SEGMEN, weights=[75, 15, 10])[0], daftar.date(), daftar))
    execute_values(cur, "INSERT INTO nasabah(nik_masked,nama,email,kota,segmen,tgl_daftar,updated_at) VALUES %s",
                   nasabah_rows)

    rekening_rows, rek_ids = [], []
    for id_n in range(1, n_nasabah + 1):
        for _ in range(random.choices([1, 2], weights=[80, 20])[0]):
            no = f"{random.randint(10**9, 10**10 - 1)}"[:10] + f"{len(rek_ids) % 100:02d}"
            rek_ids.append(no)
            rekening_rows.append((no, id_n, random.choice(PRODUK)[0], random.choice(CABANG)[0],
                                  round(random.uniform(50_000, 500_000_000), 2),
                                  (today - timedelta(days=random.randint(100, 1400))).date()))
    # buang duplikat no_rekening (kemungkinan kecil)
    rekening_rows = list({r[0]: r for r in rekening_rows}.values())
    rek_ids = [r[0] for r in rekening_rows]
    execute_values(cur, "INSERT INTO rekening(no_rekening,id_nasabah,kode_produk,kode_cabang,saldo,tgl_buka) VALUES %s",
                   rekening_rows)

    trx_rows = []
    for _ in range(n_trx):
        trx_rows.append((random.choice(rek_ids), random.choice(JENIS_TRX),
                         round(random.lognormvariate(12, 1.2), 2), random.choices(CHANNEL, weights=[25, 45, 15, 15])[0],
                         today - timedelta(seconds=random.randint(0, 90 * 86400)), None))
    execute_values(cur, "INSERT INTO transaksi(no_rekening,jenis_transaksi,nominal,channel,waktu_transaksi,keterangan) VALUES %s",
                   trx_rows, page_size=5000)
    conn.commit()
    conn.close()
    print(f"[postgres] nasabah={n_nasabah} rekening={len(rekening_rows)} transaksi={n_trx}")


def gen_mysql(n_nasabah):
    conn = mysql.connector.connect(
        host=env("MYSQL_HOST", "localhost"), port=int(env("MYSQL_PORT", "3306")),
        database="channel_banking", user="channel_user", password=env("MYSQL_PASSWORD", "change_me_mysql"))
    cur = conn.cursor()
    cur.execute("SET FOREIGN_KEY_CHECKS=0")
    cur.execute("TRUNCATE sesi_login")
    cur.execute("TRUNCATE mobile_user")
    users = [(i, random.choice(["ANDROID", "IOS"]), (datetime.now() - timedelta(days=random.randint(10, 900))).date())
             for i in range(1, n_nasabah + 1) if random.random() < 0.6]
    cur.executemany("INSERT INTO mobile_user(id_nasabah,device_type,tgl_aktivasi) VALUES (%s,%s,%s)", users)
    sesi = [(random.randint(1, len(users)), datetime.now() - timedelta(minutes=random.randint(0, 60 * 24 * 30)),
             random.randint(20, 900), int(random.random() > 0.05)) for _ in range(len(users) * 8)]
    cur.executemany("INSERT INTO sesi_login(id_user,waktu_login,durasi_detik,berhasil) VALUES (%s,%s,%s,%s)", sesi)
    conn.commit()
    conn.close()
    print(f"[mysql] mobile_user={len(users)} sesi_login={len(sesi)}")


def gen_mongo(n_nasabah, n_logs):
    client = MongoClient(host=env("MONGO_HOST", "localhost"), port=27017, username="mongo_user",
                         password=env("MONGO_PASSWORD", "change_me_mongo"))
    col = client["banking_logs"]["log_aktivitas"]
    col.drop()
    aksi = ["LOGIN", "CEK_SALDO", "TRANSFER", "BAYAR_TAGIHAN", "LOGOUT", "GANTI_PIN"]
    docs = [{"id_nasabah": random.randint(1, n_nasabah), "aksi": random.choice(aksi),
             "ip": fake.ipv4_private(), "perangkat": {"os": random.choice(["ANDROID", "IOS", "WEB"]),
                                                       "versi_app": f"{random.randint(5, 9)}.{random.randint(0, 9)}"},
             "waktu": datetime.now() - timedelta(seconds=random.randint(0, 30 * 86400)),
             "sukses": random.random() > 0.03} for _ in range(n_logs)]
    col.insert_many(docs)
    col.create_index("id_nasabah")
    print(f"[mongo] log_aktivitas={len(docs)}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--nasabah", type=int, default=5000)
    p.add_argument("--transaksi", type=int, default=200000)
    p.add_argument("--logs", type=int, default=50000)
    a = p.parse_args()
    gen_pg(a.nasabah, a.transaksi)
    gen_mysql(a.nasabah)
    gen_mongo(a.nasabah, a.logs)
    print("Selesai.")

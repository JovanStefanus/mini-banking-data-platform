"""Simulasi perubahan di sumber untuk menguji SCD2 dan incremental load.
Jalankan SEBELUM menjalankan pipeline untuk kedua kalinya.

    python -m etl.simulate_changes
"""
from datetime import datetime, timedelta

import psycopg2

from .config import _env


def main():
    # Koneksi read-write khusus simulasi (pipeline sendiri tetap read-only)
    conn = psycopg2.connect(host=_env("PG_CORE_HOST", "127.0.0.1"), port=_env("PG_CORE_PORT", "15432"),
                            dbname="core_banking", user="core_user", password=_env("PG_CORE_PASSWORD", ""))
    cur = conn.cursor()
    now = datetime.now()   # sama dengan generator: waktu lokal naive

    cur.execute("""UPDATE nasabah SET segmen = 'PRIORITAS', kota = 'Jakarta', updated_at = %s
                    WHERE id_nasabah IN (SELECT id_nasabah FROM nasabah WHERE segmen = 'RITEL'
                                         ORDER BY random() LIMIT 10)""", (now,))
    print(f"{cur.rowcount} nasabah naik segmen ke PRIORITAS")

    cur.execute("""INSERT INTO transaksi(no_rekening, jenis_transaksi, nominal, channel, waktu_transaksi, keterangan)
                   SELECT no_rekening, 'SETOR', 150000, 'MOBILE', %s, 'simulasi'
                     FROM rekening ORDER BY random() LIMIT 1000""", (now + timedelta(seconds=1),))
    print(f"{cur.rowcount} transaksi baru ditambahkan")
    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()

"""TRANSFORM + LOAD: dari staging ke star schema. Semua langkah idempotent (aman di-rerun)."""
from datetime import date

START_DATE, END_DATE = date(2020, 1, 1), date(2030, 12, 31)


def _count(cur, table):
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    return cur.fetchone()[0]


def load_dim_waktu(dwh):
    cur = dwh.cursor()
    cur.execute("""
        INSERT INTO dwh.dim_waktu (waktu_key, tanggal, hari, bulan, nama_bulan, kuartal, tahun, nama_hari, is_weekend)
        SELECT to_char(d, 'YYYYMMDD')::int, d::date,
               EXTRACT(DAY FROM d)::smallint, EXTRACT(MONTH FROM d)::smallint,
               (ARRAY['Januari','Februari','Maret','April','Mei','Juni','Juli','Agustus',
                      'September','Oktober','November','Desember'])[EXTRACT(MONTH FROM d)::int],
               EXTRACT(QUARTER FROM d)::smallint, EXTRACT(YEAR FROM d)::smallint,
               (ARRAY['Senin','Selasa','Rabu','Kamis','Jumat','Sabtu','Minggu'])[EXTRACT(ISODOW FROM d)::int],
               EXTRACT(ISODOW FROM d) >= 6
        FROM generate_series(%s::date, %s::date, interval '1 day') AS d
        ON CONFLICT (waktu_key) DO NOTHING""", (START_DATE, END_DATE))
    return (END_DATE - START_DATE).days + 1, cur.rowcount, 0


def load_dim_cabang(dwh):
    cur = dwh.cursor()
    read = _count(cur, "staging.cabang")
    cur.execute("""
        INSERT INTO dwh.dim_cabang (kode_cabang, nama_cabang, kota)
        SELECT kode_cabang, nama_cabang, kota FROM staging.cabang
        ON CONFLICT (kode_cabang) DO UPDATE
            SET nama_cabang = EXCLUDED.nama_cabang, kota = EXCLUDED.kota""")   # SCD Type 1
    return read, cur.rowcount, 0


def load_dim_produk(dwh):
    cur = dwh.cursor()
    read = _count(cur, "staging.produk")
    cur.execute("""
        INSERT INTO dwh.dim_produk (kode_produk, nama_produk, jenis)
        SELECT kode_produk, nama_produk, jenis FROM staging.produk
        ON CONFLICT (kode_produk) DO UPDATE
            SET nama_produk = EXCLUDED.nama_produk, jenis = EXCLUDED.jenis""")  # SCD Type 1
    return read, cur.rowcount, 0


def load_dim_nasabah_scd2(dwh):
    """SCD Type 2: kalau nama/kota/segmen berubah, versi lama ditutup dan versi baru dibuat."""
    cur = dwh.cursor()
    read = _count(cur, "staging.nasabah")

    # 1) Tutup versi lama yang atributnya berubah
    cur.execute("""
        UPDATE dwh.dim_nasabah d
           SET valid_to = s.updated_at, is_current = FALSE
          FROM staging.nasabah s
         WHERE d.id_nasabah = s.id_nasabah
           AND d.is_current
           AND (d.nama, d.kota, d.segmen) IS DISTINCT FROM (s.nama, s.kota, s.segmen)""")
    closed = cur.rowcount

    # 2) Buat versi baru: untuk nasabah baru DAN nasabah yang versi lamanya barusan ditutup
    cur.execute("""
        INSERT INTO dwh.dim_nasabah (id_nasabah, nama, kota, segmen, tgl_daftar, valid_from, valid_to, is_current)
        SELECT s.id_nasabah, s.nama, s.kota, s.segmen, s.tgl_daftar,
               CASE WHEN EXISTS (SELECT 1 FROM dwh.dim_nasabah x WHERE x.id_nasabah = s.id_nasabah)
                    THEN s.updated_at            -- perubahan: berlaku sejak waktu update di sumber
                    ELSE s.tgl_daftar::timestamp -- nasabah baru: berlaku sejak tanggal daftar
               END,
               TIMESTAMP '9999-12-31', TRUE
          FROM staging.nasabah s
         WHERE NOT EXISTS (SELECT 1 FROM dwh.dim_nasabah d
                            WHERE d.id_nasabah = s.id_nasabah AND d.is_current)""")
    inserted = cur.rowcount
    print(f"      SCD2: {closed} versi ditutup, {inserted} versi baru dibuat")
    return read, inserted, 0


def load_fact_transaksi(dwh):
    """Point-in-time join: transaksi dihubungkan ke versi nasabah yang berlaku saat transaksi terjadi."""
    cur = dwh.cursor()
    read = _count(cur, "staging.transaksi")
    cur.execute("""
        INSERT INTO dwh.fact_transaksi
              (id_transaksi, waktu_key, nasabah_key, produk_key, cabang_key, channel_key,
               jenis_transaksi, nominal, waktu_transaksi)
        SELECT t.id_transaksi, to_char(t.waktu_transaksi, 'YYYYMMDD')::int,
               dn.nasabah_key, dp.produk_key, dc.cabang_key, ch.channel_key,
               t.jenis_transaksi, t.nominal, t.waktu_transaksi
          FROM staging.transaksi t
          JOIN staging.rekening r  ON r.no_rekening = t.no_rekening
          JOIN dwh.dim_nasabah dn  ON dn.id_nasabah = r.id_nasabah
                                  AND t.waktu_transaksi >= dn.valid_from
                                  AND t.waktu_transaksi <  dn.valid_to
          JOIN dwh.dim_produk dp   ON dp.kode_produk = r.kode_produk
          JOIN dwh.dim_cabang dc   ON dc.kode_cabang = r.kode_cabang
          JOIN dwh.dim_channel ch  ON ch.channel = t.channel
          JOIN dwh.dim_waktu w     ON w.waktu_key = to_char(t.waktu_transaksi, 'YYYYMMDD')::int
        ON CONFLICT (id_transaksi) DO NOTHING""")
    loaded = cur.rowcount
    return read, loaded, read - loaded    # yang gagal join dihitung sebagai rejected

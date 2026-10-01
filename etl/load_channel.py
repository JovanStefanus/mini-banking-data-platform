"""TRANSFORM + LOAD untuk sumber channel dan log. Semua langkah idempotent."""


def _count(cur, table):
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    return cur.fetchone()[0]


def load_dim_mobile_user(dwh):
    """SCD Type 1: upsert; hanya baris yang benar-benar berubah yang dihitung sebagai loaded."""
    cur = dwh.cursor()
    read = _count(cur, "staging.mobile_user")
    cur.execute("""
        INSERT INTO dwh.dim_mobile_user AS t (id_user, id_nasabah, device_type, tgl_aktivasi, status)
        SELECT id_user, id_nasabah, device_type, tgl_aktivasi, status FROM staging.mobile_user
        ON CONFLICT (id_user) DO UPDATE
            SET id_nasabah = EXCLUDED.id_nasabah, device_type = EXCLUDED.device_type,
                tgl_aktivasi = EXCLUDED.tgl_aktivasi, status = EXCLUDED.status
            WHERE (t.id_nasabah, t.device_type, t.tgl_aktivasi, t.status)
                  IS DISTINCT FROM (EXCLUDED.id_nasabah, EXCLUDED.device_type,
                                    EXCLUDED.tgl_aktivasi, EXCLUDED.status)""")
    return read, cur.rowcount, 0


def load_fact_sesi_login(dwh):
    cur = dwh.cursor()
    read = _count(cur, "staging.sesi_login")
    cur.execute("""
        INSERT INTO dwh.fact_sesi_login
              (id_sesi, waktu_key, id_user, id_nasabah, waktu_login, durasi_detik, berhasil)
        SELECT s.id_sesi, to_char(s.waktu_login, 'YYYYMMDD')::int, s.id_user, m.id_nasabah,
               s.waktu_login, s.durasi_detik, (s.berhasil = 1)
          FROM staging.sesi_login s
          JOIN dwh.dim_mobile_user m ON m.id_user = s.id_user
          JOIN dwh.dim_waktu w       ON w.waktu_key = to_char(s.waktu_login, 'YYYYMMDD')::int
        ON CONFLICT (id_sesi) DO NOTHING""")
    loaded = cur.rowcount
    return read, loaded, read - loaded


def load_fact_aktivitas(dwh):
    cur = dwh.cursor()
    read = _count(cur, "staging.log_aktivitas")
    cur.execute("""
        INSERT INTO dwh.fact_aktivitas
              (id_log, waktu_key, id_nasabah, aksi, os, versi_app, waktu_aktivitas, sukses)
        SELECT a.id_log, to_char(a.waktu_aktivitas, 'YYYYMMDD')::int, a.id_nasabah, a.aksi,
               a.os, a.versi_app, a.waktu_aktivitas, a.sukses
          FROM staging.log_aktivitas a
          JOIN dwh.dim_waktu w ON w.waktu_key = to_char(a.waktu_aktivitas, 'YYYYMMDD')::int
        ON CONFLICT (id_log) DO NOTHING""")
    loaded = cur.rowcount
    return read, loaded, read - loaded

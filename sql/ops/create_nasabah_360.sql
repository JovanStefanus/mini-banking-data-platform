-- Golden record: satu baris per nasabah yang menggabungkan core banking, mobile banking, dan log aktivitas.
-- Jalankan SETELAH pipeline ETL berhasil (tabel channel harus sudah ada):
--   Get-Content sql\ops\create_nasabah_360.sql | docker exec -i mbdp_pg_dwh psql -U dwh_user -d dwh
-- Aman dijalankan berulang.

CREATE OR REPLACE VIEW semantic.v_nasabah_360 AS
SELECT n.id_nasabah,
       n.nama,
       n.kota,
       n.segmen,
       n.tgl_daftar,
       (m.id_user IS NOT NULL)          AS punya_mobile_banking,
       m.device_type,
       m.tgl_aktivasi                   AS tgl_aktivasi_mobile,
       COALESCE(t.jumlah_transaksi, 0)  AS jumlah_transaksi,
       COALESCE(t.total_nominal, 0)     AS total_nominal,
       COALESCE(l.jumlah_login, 0)      AS jumlah_login,
       l.login_terakhir,
       COALESCE(a.jumlah_aktivitas, 0)  AS jumlah_aktivitas,
       COALESCE(a.aktivitas_gagal, 0)   AS aktivitas_gagal,
       a.aktivitas_terakhir
  FROM dwh.dim_nasabah n
  LEFT JOIN dwh.dim_mobile_user m ON m.id_nasabah = n.id_nasabah
  LEFT JOIN (SELECT dn.id_nasabah, COUNT(*) AS jumlah_transaksi, SUM(f.nominal) AS total_nominal
               FROM dwh.fact_transaksi f
               JOIN dwh.dim_nasabah dn ON dn.nasabah_key = f.nasabah_key
              GROUP BY dn.id_nasabah) t ON t.id_nasabah = n.id_nasabah
  LEFT JOIN (SELECT id_nasabah, COUNT(*) AS jumlah_login, MAX(waktu_login) AS login_terakhir
               FROM dwh.fact_sesi_login
              GROUP BY id_nasabah) l ON l.id_nasabah = n.id_nasabah
  LEFT JOIN (SELECT id_nasabah, COUNT(*) AS jumlah_aktivitas,
                    COUNT(*) FILTER (WHERE NOT sukses) AS aktivitas_gagal,
                    MAX(waktu_aktivitas) AS aktivitas_terakhir
               FROM dwh.fact_aktivitas
              GROUP BY id_nasabah) a ON a.id_nasabah = n.id_nasabah
 WHERE n.is_current;

-- API membaca view ini (bi_reader sudah otomatis boleh lewat default privileges)
GRANT USAGE ON SCHEMA semantic TO api_reader;
GRANT SELECT ON semantic.v_nasabah_360 TO api_reader;

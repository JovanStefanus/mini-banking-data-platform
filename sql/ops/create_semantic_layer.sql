-- Semantic layer: view bisnis di atas star schema + user read-only untuk BI tool.
-- Jalankan sebagai superuser DWH:
--   Get-Content sql\ops\create_semantic_layer.sql | docker exec -i mbdp_pg_dwh psql -U dwh_user -d dwh -v bi_pw=PASSWORD_BI
-- Aman dijalankan berulang.

CREATE SCHEMA IF NOT EXISTS semantic;

-- 1) Tabel lebar (denormalisasi) dengan nama kolom yang mudah dipahami pengguna bisnis.
--    segmen_nasabah = segmen yang berlaku SAAT transaksi terjadi (hasil SCD2).
CREATE OR REPLACE VIEW semantic.v_transaksi AS
SELECT f.id_transaksi,
       w.tanggal,
       w.tahun,
       w.nama_bulan,
       w.nama_hari,
       w.is_weekend,
       f.waktu_transaksi,
       n.id_nasabah,
       n.nama    AS nama_nasabah,
       n.segmen  AS segmen_nasabah,
       n.kota    AS kota_nasabah,
       p.nama_produk,
       p.jenis   AS jenis_produk,
       c.nama_cabang,
       c.kota    AS kota_cabang,
       ch.channel,
       f.jenis_transaksi,
       f.nominal
  FROM dwh.fact_transaksi f
  JOIN dwh.dim_waktu    w  ON w.waktu_key    = f.waktu_key
  JOIN dwh.dim_nasabah  n  ON n.nasabah_key  = f.nasabah_key
  JOIN dwh.dim_produk   p  ON p.produk_key   = f.produk_key
  JOIN dwh.dim_cabang   c  ON c.cabang_key   = f.cabang_key
  JOIN dwh.dim_channel  ch ON ch.channel_key = f.channel_key;

-- 2) Metrik bisnis. Definisinya ditulis SEKALI di sini, dipakai semua laporan.
CREATE OR REPLACE VIEW semantic.v_ringkasan_harian AS
SELECT tanggal,
       COUNT(*)                 AS jumlah_transaksi,
       SUM(nominal)             AS total_nominal,
       ROUND(AVG(nominal), 2)   AS rata_rata_nominal
  FROM semantic.v_transaksi
 GROUP BY tanggal;

CREATE OR REPLACE VIEW semantic.v_kinerja_cabang AS
SELECT nama_cabang,
       kota_cabang,
       COUNT(*)                 AS jumlah_transaksi,
       SUM(nominal)             AS total_nominal,
       ROUND(AVG(nominal), 2)   AS rata_rata_nominal
  FROM semantic.v_transaksi
 GROUP BY nama_cabang, kota_cabang;

CREATE OR REPLACE VIEW semantic.v_channel_mix AS
SELECT channel,
       COUNT(*)                                          AS jumlah_transaksi,
       SUM(nominal)                                      AS total_nominal,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS persen_transaksi
  FROM semantic.v_transaksi
 GROUP BY channel;

CREATE OR REPLACE VIEW semantic.v_produk_ranking AS
SELECT nama_produk,
       jenis_produk,
       COUNT(*)                                        AS jumlah_transaksi,
       SUM(nominal)                                    AS total_nominal,
       RANK() OVER (ORDER BY SUM(nominal) DESC)        AS peringkat
  FROM semantic.v_transaksi
 GROUP BY nama_produk, jenis_produk;

CREATE OR REPLACE VIEW semantic.v_segmen_nasabah AS
SELECT segmen_nasabah,
       COUNT(DISTINCT id_nasabah) AS jumlah_nasabah,
       COUNT(*)                   AS jumlah_transaksi,
       SUM(nominal)               AS total_nominal
  FROM semantic.v_transaksi
 GROUP BY segmen_nasabah;

-- 3) User untuk BI tool: hanya boleh membaca schema semantic (least privilege).
--    Ia TIDAK punya akses ke schema dwh, staging, maupun audit.
SELECT format('CREATE ROLE bi_reader LOGIN PASSWORD %L', :'bi_pw')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'bi_reader')
\gexec

ALTER ROLE bi_reader PASSWORD :'bi_pw';

GRANT CONNECT ON DATABASE dwh TO bi_reader;
GRANT USAGE ON SCHEMA semantic TO bi_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA semantic TO bi_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA semantic GRANT SELECT ON TABLES TO bi_reader;

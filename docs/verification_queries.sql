-- Jalankan di DBeaver pada koneksi DWH (port 5433)

-- 1. Monitoring pipeline: status tiap langkah
SELECT run_id, target_table, status, rows_read, rows_loaded, rows_rejected,
       finished_at - started_at AS durasi
FROM audit.etl_audit_log ORDER BY run_id DESC LIMIT 12;

-- 2. Hasil data quality check
SELECT run_id, check_name, passed, detail FROM audit.dq_check_result ORDER BY id DESC LIMIT 8;

-- 3. Riwayat SCD2: nasabah yang punya lebih dari satu versi
SELECT id_nasabah, nama, segmen, kota, valid_from, valid_to, is_current
FROM dwh.dim_nasabah
WHERE id_nasabah IN (SELECT id_nasabah FROM dwh.dim_nasabah GROUP BY id_nasabah HAVING COUNT(*) > 1)
ORDER BY id_nasabah, valid_from;

-- 4. Produk teratas berdasarkan nominal, dengan window function RANK
SELECT p.nama_produk, SUM(f.nominal) AS total_nominal,
       RANK() OVER (ORDER BY SUM(f.nominal) DESC) AS peringkat
FROM dwh.fact_transaksi f JOIN dwh.dim_produk p USING (produk_key)
GROUP BY p.nama_produk ORDER BY peringkat;

-- 5. Volume transaksi harian dan pertumbuhan dibanding hari sebelumnya (LAG)
WITH harian AS (
    SELECT w.tanggal, COUNT(*) AS jumlah
    FROM dwh.fact_transaksi f JOIN dwh.dim_waktu w USING (waktu_key)
    GROUP BY w.tanggal)
SELECT tanggal, jumlah,
       ROUND(100.0 * (jumlah - LAG(jumlah) OVER (ORDER BY tanggal)) / NULLIF(LAG(jumlah) OVER (ORDER BY tanggal), 0), 1) AS growth_pct
FROM harian ORDER BY tanggal DESC LIMIT 14;

-- 6. Transaksi per segmen nasabah dan channel
SELECT n.segmen, c.channel, COUNT(*) AS jumlah, SUM(f.nominal) AS total
FROM dwh.fact_transaksi f
JOIN dwh.dim_nasabah n USING (nasabah_key)
JOIN dwh.dim_channel c USING (channel_key)
GROUP BY n.segmen, c.channel ORDER BY n.segmen, total DESC;

SELECT n.id_nasabah, n.segmen, n.is_current, COUNT(*) AS jumlah_transaksi
FROM dwh.fact_transaksi f
JOIN dwh.dim_nasabah n USING (nasabah_key)
WHERE n.id_nasabah IN (SELECT id_nasabah FROM dwh.dim_nasabah GROUP BY id_nasabah HAVING COUNT(*) > 1)
GROUP BY n.id_nasabah, n.segmen, n.is_current
ORDER BY n.id_nasabah, n.is_current;
# Runbook: pipeline ETL gagal

Berlaku untuk DAG `core_to_dwh_daily` di Airflow. Pipeline bersifat **idempotent**, jadi aman dijalankan ulang kapan saja.

## 1. Lihat apa yang gagal
1. Buka Airflow (`http://localhost:8090`) → **Dags** → `core_to_dwh_daily` → run yang berwarna merah.
2. Perhatikan task yang merah:

| Task | Artinya |
|---|---|
| `cek_koneksi` | Salah satu database tidak bisa dihubungi |
| `jalankan_pipeline_etl` | Salah satu langkah ETL atau data quality check gagal |
| `ringkas_audit` | Ada langkah berstatus `FAILED` di audit log |

3. Buka tab **Logs** pada task itu dan baca baris `[GAGAL]` atau `[FAILED]` paling bawah.

## 2. Periksa audit log dan data quality
Jalankan di koneksi DWH (port 5433):

```sql
-- langkah terakhir yang tercatat
SELECT run_id, target_table, status, rows_read, rows_loaded, rows_rejected, error_message
FROM audit.etl_audit_log ORDER BY run_id DESC LIMIT 20;

-- hasil data quality check
SELECT run_id, check_name, passed, detail
FROM audit.dq_check_result ORDER BY id DESC LIMIT 10;
```

## 3. Penyebab umum dan tindakan

| Gejala | Kemungkinan penyebab | Tindakan |
|---|---|---|
| `cek_koneksi` gagal untuk satu database | Container database mati | `docker compose ps`, lalu `docker compose up -d NAMA_SERVICE` |
| `password authentication failed` | Password di `.env` berbeda dengan password database | Samakan password, lalu buat ulang container yang bersangkutan |
| Data quality `FAIL` pada rekonsiliasi | Sumber berubah saat pipeline berjalan, atau ada baris lama yang diubah | Jalankan ulang; kalau tetap gagal, bandingkan jumlah baris sumber dan DWH |
| `rows_rejected` tinggi di `staging.log_aktivitas` | Dokumen MongoDB tidak lengkap | Periksa sistem penghasil log |
| Task `Timeout` | Data sangat besar atau database lambat | Periksa beban database sebelum menaikkan timeout |

## 4. Menjalankan ulang
- Di Airflow: buka task yang gagal → **Clear** (task akan diulang), atau **Trigger** DAG dari awal.
- Retry otomatis sudah diatur 3 kali dengan jeda 5 menit, jadi gangguan singkat biasanya pulih sendiri.

## 5. Setelah selesai
Catat penyebab dan tindakannya (tanggal, gejala, akar masalah, perbaikan). Kalau penyebabnya baru, tambahkan ke tabel di atas.

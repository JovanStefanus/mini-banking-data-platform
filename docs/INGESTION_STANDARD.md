# Standar Ingestion Data (draft)

## 1. Penamaan
- Schema: `staging` (mentah), `dwh` (star schema), `audit` (monitoring)
- Tabel dimensi `dim_*`, fakta `fact_*`, huruf kecil snake_case
- DAG: `<sumber>_to_<target>_<frekuensi>`, contoh `core_to_dwh_daily`

## 2. Aturan load
- Dimensi: incremental berdasarkan `updated_at`; `dim_nasabah` memakai SCD Type 2
- Fakta: idempotent (`ON CONFLICT (id_transaksi) DO NOTHING`), aman di-rerun
- Setiap run wajib menulis ke `audit.etl_audit_log`

## 3. Data quality minimum
- Tidak ada NULL pada business key
- Tidak ada duplikat `id_transaksi`
- Jumlah baris fakta = jumlah baris sumber (rekonsiliasi)
- Nominal > 0

## 4. Error handling
- Baris ditolak dicatat (`rows_rejected`), pipeline gagal jika reject > ambang batas
- Retry 3x dengan jeda 5 menit, lalu status `FAILED` + alert

## 5. Keamanan
- Hanya data sintetis; NIK dimasking; kredensial via `.env`, tidak masuk Git

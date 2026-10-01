# Mini Banking Data Platform

[![CI](https://github.com/JovanStefanus/mini-banking-data-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/JovanStefanus/mini-banking-data-platform/actions/workflows/ci.yml)

Simulasi platform data ala perbankan: data dari beberapa sumber diproses lewat pipeline ETL ke **data warehouse (star schema)**, lengkap dengan **SCD Type 2**, **incremental load**, **audit log**, dan **data quality check**. Data warehouse dilayani lewat **REST API** (Java Spring Boot), **semantic layer + dashboard** (Metabase), dan **data virtualization** (Trino).

> **Semua data adalah data sintetis** (dibuat dengan Faker). Tidak ada data nasabah asli, dan NIK sudah dimasking.

Project portofolio untuk peran Data Engineer / Developer.

## Status

- [x] **Fase 1** – Source database (PostgreSQL, MySQL, MongoDB), skema DWH, generator data sintetis
- [x] **Fase 2** – Pipeline ETL ke DWH (SCD2, incremental load, audit log, data quality)
- [x] **Fase 3** – REST API Java Spring Boot (transaksi, master data nasabah, ringkasan harian)
- [x] **Fase 4a** – Semantic layer (view bisnis) dan dashboard Metabase
- [x] **Fase 4b** – Data virtualization dengan Trino (query lintas PostgreSQL, MySQL, MongoDB)
- [x] **Fase 5a** – MySQL dan MongoDB dimuat ke DWH, golden record nasabah, endpoint profil 360
- [ ] **Fase 5b** – Orkestrasi dengan Airflow (penjadwalan dan monitoring pipeline)
- [x] **Fase 5c** – Unit test, dokumentasi OpenAPI/Swagger, GitHub Actions (CI)
- [ ] **Fase 6** – Oracle/SQL Server sebagai sumber tambahan, Kubernetes (opsional)

## Arsitektur

```
 Source systems             ETL (Python)        Data Warehouse (PostgreSQL)            Serving
┌────────────────┐       ┌──────────────┐      ┌─────────────────────────────┐    ┌──────────────────┐
│ PostgreSQL     │       │ Extract      │      │ staging  (data mentah)      │    │ REST API         │
│ core banking   │──────►│ Transform    │─────►│ dwh      (star schema)      │───►│ Java Spring Boot │
├────────────────┤       │ & Load       │      │ semantic (view bisnis)      │───►│ Metabase         │
│ MySQL (channel)│  ...  │ Data quality │      │ audit    (monitoring ETL)   │    │ (dashboard)      │
│ MongoDB (log)  │       │ Audit log    │      └─────────────────────────────┘    └──────────────────┘
└───────▲────────┘       └──────────────┘
        │
        └── Trino (data virtualization): query lintas sumber tanpa memindahkan data
```

Pipeline ETL memuat data dari **tiga sumber**: PostgreSQL core banking, MySQL (mobile banking), dan MongoDB (log aktivitas). Trino juga dapat membaca ketiganya langsung tanpa memindahkan data.

## Tech stack

| Area | Teknologi |
|---|---|
| Database | PostgreSQL 16, MySQL 8.4, MongoDB 7 |
| ETL | Python (psycopg2, mysql-connector, pymongo), SQL |
| REST API | Java 17, Spring Boot 4.1, JdbcTemplate, Maven |
| BI / dashboard | Metabase |
| Data virtualization | Trino |
| Infrastruktur | Docker, Docker Compose |
| Data sintetis | Faker |
| Pengujian | JUnit 5 dan Mockito (Java), pytest (Python) |
| CI | GitHub Actions |
| Version control | Git, GitHub |

## Model data

Star schema dengan `fact_transaksi` di tengah:

| Tabel | Jenis | Catatan |
|---|---|---|
| `fact_transaksi` | Fakta | Kunci `id_transaksi` dipakai untuk idempotensi |
| `dim_waktu` | Dimensi | 2020–2030, kunci `YYYYMMDD` |
| `dim_nasabah` | Dimensi | **SCD Type 2** (`valid_from`, `valid_to`, `is_current`) |
| `dim_produk` | Dimensi | SCD Type 1 |
| `dim_cabang` | Dimensi | SCD Type 1 |
| `dim_channel` | Dimensi | ATM, MOBILE, INTERNET, TELLER |
| `dim_mobile_user` | Dimensi | Akun mobile banking (dari MySQL), SCD Type 1 |
| `fact_sesi_login` | Fakta | Sesi login mobile banking (dari MySQL), kunci `id_sesi` |
| `fact_aktivitas` | Fakta | Log aktivitas nasabah (dari MongoDB), kunci `id_log` (ObjectId) |

Tabel monitoring ada di schema `audit`: `etl_audit_log` dan `dq_check_result`.

## Fitur pipeline ETL

- **Incremental load**: transaksi diambil berdasarkan watermark `id_transaksi`, bukan seluruh tabel.
- **Idempotent**: pipeline aman dijalankan ulang (`ON CONFLICT DO NOTHING` + watermark) tanpa membuat data ganda.
- **SCD Type 2** pada `dim_nasabah`: perubahan nama, kota, atau segmen menutup versi lama dan membuat versi baru.
- **Point-in-time join**: transaksi dihubungkan ke versi nasabah yang berlaku saat transaksi terjadi.
- **Audit log**: setiap langkah mencatat status, jumlah baris dibaca/dimuat/ditolak, dan durasi.
- **Data quality check**: cek NULL, satu versi current per nasabah, nominal > 0, dan rekonsiliasi jumlah baris serta total nominal terhadap sumber.
- **Multi-source**: PostgreSQL (core banking), MySQL (mobile banking), dan MongoDB (log aktivitas) dimuat dalam satu pipeline.
- **Watermark per sumber**: `id_transaksi` (PostgreSQL), `id_sesi` (MySQL), dan `_id` ObjectId (MongoDB).
- **Validasi saat ingestion**: dokumen MongoDB yang tidak lengkap ditolak dan dihitung sebagai `rejected`.
- **Data minimization**: alamat IP dari log aktivitas tidak dimuat ke DWH.
- **Koneksi sumber read-only**: koneksi ke PostgreSQL dan MySQL dibuat read-only; ETL hanya membaca dari MongoDB.

Konvensi lengkap ada di [`docs/INGESTION_STANDARD.md`](docs/INGESTION_STANDARD.md).

## Semantic layer dan dashboard

Schema `semantic` berisi view bisnis di atas star schema. Definisi metrik ditulis **sekali** di view, sehingga semua laporan memakai angka yang sama dan analis tidak perlu memahami join star schema.

| View | Isi |
|---|---|
| `v_transaksi` | Tabel lebar (fakta + dimensi) dengan nama kolom yang mudah dipahami |
| `v_ringkasan_harian` | Jumlah, total, dan rata-rata nominal per hari |
| `v_kinerja_cabang` | Jumlah dan total nominal per cabang |
| `v_channel_mix` | Komposisi transaksi per channel (dengan persentase) |
| `v_produk_ranking` | Peringkat produk berdasarkan total nominal |
| `v_segmen_nasabah` | Jumlah nasabah, transaksi, dan nominal per segmen |
| `v_nasabah_360` | **Golden record**: profil nasabah dari core banking, mobile banking, dan log aktivitas |

`segmen_nasabah` adalah segmen yang berlaku **saat transaksi terjadi** (hasil SCD Type 2).

Metabase memakai user `bi_reader` yang hanya boleh membaca schema `semantic`, tanpa akses ke `dwh`, `staging`, maupun `audit`.

![Dashboard](docs/images/dashboard.png)

### Menjalankan semantic layer dan Metabase

```powershell
# 1. Tambahkan BI_DB_PASSWORD di .env, lalu buat semantic layer dan user bi_reader (sekali saja)
Get-Content sql\ops\create_semantic_layer.sql | docker exec -i mbdp_pg_dwh psql -U dwh_user -d dwh -v bi_pw=PASSWORD_BI

# 2. Jalankan Metabase, lalu buka http://localhost:3000
docker compose up -d
```

Saat menambahkan database di Metabase: Host `postgres_dwh`, Port `5432`, Database `dwh`, Username `bi_reader`, Schemas → *Only these...* → `semantic`.

## Golden record (Master Data Management)

View `semantic.v_nasabah_360` menghasilkan **satu baris per nasabah** yang menggabungkan tiga sistem yang masing-masing hanya tahu sebagian:

| Sumber | Informasi |
|---|---|
| PostgreSQL (core banking) | Identitas, kota, segmen, jumlah dan total transaksi |
| MySQL (mobile banking) | Status dan perangkat mobile banking, jumlah dan waktu login terakhir |
| MongoDB (log aktivitas) | Jumlah aktivitas, aktivitas gagal, dan aktivitas terakhir |

API menyajikannya di `GET /api/v1/nasabah/{id}/profil`. Endpoint ini membaca dari semantic layer, sehingga definisi metrik tidak diduplikasi di kode API.

```powershell
# Jalankan setelah pipeline ETL berhasil
Get-Content sql\ops\create_nasabah_360.sql | docker exec -i mbdp_pg_dwh psql -U dwh_user -d dwh
```

![Profil nasabah 360 lewat API](docs/images/golden_record_api.png)
![Pipeline dengan sumber channel](docs/images/pipeline_channel.png)

## Data virtualization (Trino)

Trino menjalankan **satu query SQL yang menggabungkan beberapa sumber tanpa memindahkan data**. Empat catalog dikonfigurasi di folder `trino/catalog/`:

| Catalog | Sumber |
|---|---|
| `core` | PostgreSQL core banking |
| `mysql` | MySQL channel banking |
| `mongodb` | MongoDB log aktivitas |
| `dwh` | Data warehouse (hanya schema `semantic`, lewat `bi_reader`) |

Contoh query lintas sumber ada di [`trino/queries/`](trino/queries/):

| File | Menggabungkan |
|---|---|
| `02_postgres_mysql.sql` | PostgreSQL + MySQL: adopsi mobile banking per segmen nasabah |
| `03_postgres_mongodb.sql` | PostgreSQL + MongoDB: aktivitas gagal per kota nasabah |
| `04_tiga_sumber.sql` | DWH + PostgreSQL + MySQL dalam satu query |

```powershell
docker compose up -d
Get-Content trino\queries\04_tiga_sumber.sql | docker exec -i mbdp_trino trino --output-format ALIGNED
```

Antarmuka web Trino ada di `http://localhost:8085` (username bebas, tanpa password).

![Query lintas sumber](docs/images/trino_federated.png)
![Antarmuka Trino](docs/images/trino_ui.png)

## REST API

API membaca data dari DWH memakai user database `api_reader` yang hanya punya hak `SELECT` di schema `dwh` dan satu view di schema `semantic` (`v_nasabah_360`).

| Endpoint | Fungsi |
|---|---|
| `GET /api/v1/transaksi?tanggal=&channel=&page=&size=` | Transaksi per tanggal, dengan paginasi (maks 200 per halaman) |
| `GET /api/v1/nasabah/{id}` | Master data nasabah (versi current) |
| `GET /api/v1/nasabah/{id}/riwayat` | Riwayat versi nasabah (SCD Type 2) |
| `GET /api/v1/nasabah/{id}/profil` | Profil 360 nasabah (golden record dari tiga sumber) |
| `GET /api/v1/ringkasan/harian?dari=&sampai=` | Jumlah dan total nominal transaksi per hari |
| `GET /actuator/health` | Status aplikasi |

Format tanggal `YYYY-MM-DD`. Nilai `channel`: `ATM`, `MOBILE`, `INTERNET`, `TELLER`. Input tidak valid menghasilkan `400` dengan pesan jelas, dan id yang tidak ada menghasilkan `404`.

Dokumentasi interaktif (OpenAPI) tersedia di `http://localhost:8080/swagger.html` saat API berjalan. Tampilan Swagger UI dimuat dari CDN, jadi butuh koneksi internet.

![Swagger UI](docs/images/swagger_ui.png)

### Menjalankan API

Prasyarat: JDK 17, dan database sudah berjalan dengan data hasil ETL.

```powershell
# 1. Tambahkan API_DB_PASSWORD di .env, lalu buat user read-only (sekali saja)
Get-Content sql\ops\create_api_reader.sql | docker exec -i mbdp_pg_dwh psql -U dwh_user -d dwh -v api_pw=PASSWORD_API

# 2. Muat .env ke terminal, lalu jalankan API
Get-Content .\.env | ForEach-Object { if ($_ -match '^\s*([^#=]+)=(.*)$') { [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), 'Process') } }
cd api
.\mvnw.cmd spring-boot:run
```

Contoh: buka `http://localhost:8080/api/v1/ringkasan/harian` untuk melihat tanggal yang punya data, lalu `http://localhost:8080/api/v1/transaksi?tanggal=YYYY-MM-DD&size=5`.

## Cara menjalankan ETL

### Prasyarat
- Docker Desktop (mesin berstatus *running*)
- Python 3.12 atau lebih baru (teruji di 3.14)
- Git

### Langkah (PowerShell, Windows)

```powershell
# 1. Siapkan konfigurasi. Ganti semua password di .env
copy .env.example .env

# 2. Jalankan database
docker compose up -d
docker compose ps

# 3. Siapkan Python
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r data_generator/requirements.txt

# 4. Muat .env ke terminal (ulangi setiap membuka terminal baru)
Get-Content .\.env | ForEach-Object { if ($_ -match '^\s*([^#=]+)=(.*)$') { [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), 'Process') } }

# 5. Isi data sintetis ke database sumber
python data_generator/generate.py --nasabah 500 --transaksi 20000 --logs 5000

# 6. Jalankan pipeline ETL
python -m etl.run_pipeline
```

Untuk Linux/macOS, ganti langkah 4 dengan `set -a; source .env; set +a`.

> Metabase dan Trino masing-masing butuh sekitar 1–2 GB RAM. Di laptop dengan RAM 8 GB, jalankan salah satunya saja (`docker compose stop metabase` atau `docker compose stop trino`).

### Port

| Service | Port di laptop |
|---|---|
| PostgreSQL core banking | 15432 |
| PostgreSQL DWH | 5433 |
| MySQL channel | 3307 |
| MongoDB | 27017 |
| REST API | 8080 |
| Metabase | 3000 |
| Trino | 8085 |

Port database sengaja tidak memakai nilai default agar tidak bentrok dengan database lokal. Kalau kamu mengubah port, ubah di `docker-compose.yml` **dan** `.env`.

## Pengujian ETL

```powershell
python -m etl.run_pipeline        # load awal
python -m etl.run_pipeline        # run ulang: tidak ada baris baru (idempotent)
python -m etl.simulate_changes    # ubah segmen nasabah + tambah transaksi di sumber
python -m etl.run_pipeline        # SCD2 membuat versi baru, transaksi baru masuk
python -m etl.simulate_channel    # tambah sesi login (MySQL) dan log aktivitas (MongoDB) baru
python -m etl.run_pipeline        # hanya data baru yang dimuat
```

Hasil pengujian:

| Skenario | Hasil |
|---|---|
| Load awal | 20.000 transaksi dimuat, semua data quality check lulus |
| Run ulang | 0 baris baru, 0 versi SCD2 baru |
| Setelah simulasi | 10 versi SCD2 ditutup dan dibuat baru, 594 transaksi baru masuk, rekonsiliasi sumber = fact (20.594 baris) |
| Load sumber channel | 292 akun mobile, 2.336 sesi login, dan 5.000 log aktivitas dimuat; semua data quality check lulus |
| Incremental channel | 100 sesi login dan 100 log baru masuk; rekonsiliasi sumber = fact |

Kumpulan query untuk memverifikasi hasil (riwayat SCD2, audit log, window function `RANK` dan `LAG`) ada di [`docs/verification_queries.sql`](docs/verification_queries.sql).

![Riwayat SCD2](docs/images/scd2_history.png)
![Audit log](docs/images/audit_log.png)

## Unit test dan CI

| Area | Cakupan | Perintah |
|---|---|---|
| API (Java, JUnit 5 + Mockito) | Validasi controller (batas `size`/`page`, channel, rentang tanggal), penanganan error 400/404/500 tanpa membocorkan detail internal, dan pengecekan bahwa dokumentasi OpenAPI memuat semua endpoint | `cd api` lalu `.\mvnw.cmd test` |
| ETL dan generator (Python, pytest) | Extract MongoDB (IP tidak dimuat, dokumen tidak lengkap ditolak, watermark), generator data selalu sejalan dengan `CHECK` constraint di skema SQL, dan konfigurasi | `python -m pytest -q` |

GitHub Actions ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) menjalankan tiga pekerjaan pada setiap push ke `main` dan setiap pull request:

1. **API**: build dan unit test dengan Java 17 dan Maven.
2. **ETL**: cek sintaks dan unit test Python.
3. **Docker Compose**: validasi konfigurasi `docker-compose.yml` beserta file yang di-`include`.

Unit test sengaja tidak memakai database: repository dan koneksi diganti objek tiruan, sehingga tes cepat dan tidak butuh Docker.

## Struktur repository

```
.
├── docker-compose.yml
├── docker-compose.bi.yml       # Metabase
├── docker-compose.trino.yml    # Trino
├── .env.example
├── .github/workflows/ci.yml    # GitHub Actions (CI)
├── pytest.ini
├── requirements-dev.txt
├── tests/                      # unit test Python
├── data_generator/             # generator data sintetis
├── etl/                        # pipeline ETL
│   ├── extract.py              # sumber PostgreSQL
│   ├── extract_channel.py      # sumber MySQL dan MongoDB
│   ├── transform_load.py
│   ├── load_channel.py
│   ├── data_quality.py
│   ├── data_quality_channel.py
│   ├── audit.py
│   ├── run_pipeline.py
│   ├── simulate_changes.py
│   ├── simulate_channel.py
│   └── sql/staging.sql
├── api/                        # REST API (Spring Boot)
│   ├── src/main/java/dev/minibank/api/
│   │   ├── controller/
│   │   ├── repository/
│   │   ├── model/
│   │   └── error/
│   ├── src/main/resources/static/   # openapi.yaml dan swagger.html
│   └── src/test/java/               # unit test
├── trino/                      # konfigurasi data virtualization
│   ├── catalog/                #   koneksi ke tiap sumber
│   ├── queries/                #   contoh query lintas sumber
│   └── access-control.properties
├── sql/                        # skema database
│   ├── source_postgres/        #   (dijalankan otomatis saat container pertama kali dibuat)
│   ├── source_mysql/
│   ├── dwh/
│   └── ops/                    #   skrip manual: user read-only API, semantic layer, golden record
└── docs/
    ├── INGESTION_STANDARD.md
    ├── verification_queries.sql
    └── images/
```

## Keputusan desain

- **Star schema** dipilih agar query analitik sederhana dan cepat (sedikit join, dimensi mudah dipahami pengguna bisnis).
- **SCD Type 2 untuk nasabah** agar analisis historis tetap akurat: transaksi lama tetap terhubung ke segmen nasabah saat itu, bukan segmen terbaru.
- **Staging schema** memisahkan proses extract dari transformasi, sehingga transformasi bisa dijalankan ulang tanpa membaca sumber lagi.
- **Audit log memakai koneksi terpisah** (autocommit) supaya catatan `FAILED` tetap tersimpan walaupun transaksi ETL di-rollback.
- **Python murni sebelum Airflow**: logika ETL dibuat dan dipahami dulu, baru dibungkus orkestrator.
- **API memakai user database read-only** (least privilege): kalau API bermasalah, data DWH tetap tidak bisa diubah. Pool koneksi juga diset read-only, dan API tidak punya akses ke schema `staging` maupun `audit`.
- **`JdbcTemplate` dipilih, bukan JPA**, karena query berupa join star schema yang bersifat analitik dan hanya-baca, sehingga SQL langsung lebih jelas dan mudah dioptimasi.
- **Semantic layer berupa view**: metrik didefinisikan sekali dan dipakai semua laporan; BI tool hanya melihat view, bukan tabel mentah.
- **ETL dan data virtualization dipakai bersama**: ETL untuk data yang sering dianalisis (performa stabil, tanpa membebani sumber), Trino untuk analisis cepat lintas sistem tanpa menyalin data.
- **Golden record berupa view di semantic layer**: satu definisi profil nasabah dipakai API dan BI, dan selalu mengikuti data terbaru di DWH.
- **Fakta channel memakai `id_nasabah` (business key)**, bukan surrogate key versi nasabah, karena sumbernya tidak mencatat versi nasabah.
- **Unit test tanpa database dan CI otomatis**: setiap perubahan diuji dan divalidasi di GitHub Actions sebelum masuk `main`, sehingga perubahan yang merusak ketahuan lebih awal.
- **Dokumentasi OpenAPI ditulis manual**, dengan satu unit test yang menjaganya agar tidak ketinggalan dari endpoint. Library otomatis (springdoc) belum dipakai karena kompatibilitasnya dengan Spring Boot 4.1 belum terkonfirmasi.

## Keterbatasan yang diketahui

- Watermark berbasis `id_transaksi` tidak menangkap perubahan pada transaksi lama atau data yang datang terlambat.
- Kolom `loaded` pada dimensi SCD Type 1 menghitung baris yang di-upsert, bukan yang benar-benar berubah.
- Orkestrasi ETL masih manual (belum ada penjadwalan otomatis).
- Fakta channel (`fact_sesi_login`, `fact_aktivitas`) belum terhubung ke versi historis nasabah, sehingga analisis per segmen pada saat kejadian hanya tersedia untuk transaksi.
- Watermark MongoDB memakai `_id`, sehingga dokumen lama yang diubah tidak ikut diperbarui.
- Golden record menganggap satu nasabah punya paling banyak satu akun mobile banking.
- API belum punya autentikasi/otorisasi dan caching. Dokumentasi OpenAPI ditulis manual (dijaga oleh satu unit test), bukan dihasilkan otomatis.
- Unit test memakai objek tiruan; belum ada integration test yang menjalankan pipeline dan API terhadap database sungguhan di CI.
- Dashboard dibuat manual di Metabase dan belum disimpan sebagai kode; Metabase memakai database internal H2 (cukup untuk demo, bukan produksi).
- Trino dikunci read-only di level sistem, tetapi catalog `core`, `mysql`, dan `mongodb` masih memakai akun pemilik database. Untuk produksi, gunakan user read-only per sumber.
- Query Trino membebani sistem sumber dan tidak cocok untuk query berat yang berulang.
- Metabase dan Trino cukup berat di laptop dengan RAM terbatas.
- Data sintetis dibuat acak, sehingga distribusinya tidak mencerminkan pola nyata.

## Keamanan

- Hanya data sintetis, tidak ada data pribadi asli.
- NIK disimpan dalam bentuk masking.
- Kredensial dibaca dari `.env` dan tidak masuk Git (`.env` ada di `.gitignore`); konfigurasi Trino membaca password lewat `${ENV:...}`.
- Koneksi ETL ke PostgreSQL dan MySQL bersifat read-only.
- Alamat IP dari log aktivitas tidak dimuat ke DWH (data minimization).
- API memakai user `api_reader` dan BI tool memakai user `bi_reader`, masing-masing dengan hak `SELECT` yang dibatasi; semua nilai query API lewat placeholder (bukan digabung ke string SQL), dan pesan error tidak membocorkan detail internal.
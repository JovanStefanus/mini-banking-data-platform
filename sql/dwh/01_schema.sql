-- Data Warehouse: star schema
CREATE SCHEMA IF NOT EXISTS staging;   -- data mentah hasil extract
CREATE SCHEMA IF NOT EXISTS dwh;       -- star schema
CREATE SCHEMA IF NOT EXISTS audit;     -- monitoring pipeline

-- ===== Dimensi =====
CREATE TABLE dwh.dim_waktu (
    waktu_key    INT PRIMARY KEY,          -- format YYYYMMDD
    tanggal      DATE NOT NULL UNIQUE,
    hari         SMALLINT NOT NULL,
    bulan        SMALLINT NOT NULL,
    nama_bulan   VARCHAR(15) NOT NULL,
    kuartal      SMALLINT NOT NULL,
    tahun        SMALLINT NOT NULL,
    nama_hari    VARCHAR(10) NOT NULL,
    is_weekend   BOOLEAN NOT NULL
);

CREATE TABLE dwh.dim_cabang (
    cabang_key   SERIAL PRIMARY KEY,
    kode_cabang  VARCHAR(5) NOT NULL UNIQUE,
    nama_cabang  VARCHAR(100) NOT NULL,
    kota         VARCHAR(50) NOT NULL
);

CREATE TABLE dwh.dim_produk (
    produk_key   SERIAL PRIMARY KEY,
    kode_produk  VARCHAR(5) NOT NULL UNIQUE,
    nama_produk  VARCHAR(100) NOT NULL,
    jenis        VARCHAR(20) NOT NULL
);

-- SCD Type 2: riwayat perubahan segmen/kota nasabah tetap tersimpan
CREATE TABLE dwh.dim_nasabah (
    nasabah_key    SERIAL PRIMARY KEY,     -- surrogate key
    id_nasabah     INT NOT NULL,           -- natural/business key
    nama           VARCHAR(100) NOT NULL,
    kota           VARCHAR(50),
    segmen         VARCHAR(20) NOT NULL,
    tgl_daftar     DATE NOT NULL,
    valid_from     TIMESTAMP NOT NULL,
    valid_to       TIMESTAMP NOT NULL DEFAULT '9999-12-31',
    is_current     BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE INDEX idx_dim_nasabah_bk ON dwh.dim_nasabah(id_nasabah, is_current);

CREATE TABLE dwh.dim_channel (
    channel_key  SERIAL PRIMARY KEY,
    channel      VARCHAR(15) NOT NULL UNIQUE
);

-- ===== Fakta =====
CREATE TABLE dwh.fact_transaksi (
    id_transaksi     BIGINT PRIMARY KEY,   -- degenerate dimension, juga kunci idempotensi
    waktu_key        INT NOT NULL REFERENCES dwh.dim_waktu(waktu_key),
    nasabah_key      INT NOT NULL REFERENCES dwh.dim_nasabah(nasabah_key),
    produk_key       INT NOT NULL REFERENCES dwh.dim_produk(produk_key),
    cabang_key       INT NOT NULL REFERENCES dwh.dim_cabang(cabang_key),
    channel_key      INT NOT NULL REFERENCES dwh.dim_channel(channel_key),
    jenis_transaksi  VARCHAR(15) NOT NULL,
    nominal          NUMERIC(18,2) NOT NULL,
    waktu_transaksi  TIMESTAMP NOT NULL,
    loaded_at        TIMESTAMP NOT NULL DEFAULT now()
);
CREATE INDEX idx_fact_waktu    ON dwh.fact_transaksi(waktu_key);
CREATE INDEX idx_fact_nasabah  ON dwh.fact_transaksi(nasabah_key);

-- ===== Monitoring pipeline =====
CREATE TABLE audit.etl_audit_log (
    run_id        BIGSERIAL PRIMARY KEY,
    pipeline_name VARCHAR(100) NOT NULL,
    target_table  VARCHAR(100) NOT NULL,
    status        VARCHAR(10) NOT NULL CHECK (status IN ('RUNNING','SUCCESS','FAILED')),
    rows_read     BIGINT,
    rows_loaded   BIGINT,
    rows_rejected BIGINT,
    started_at    TIMESTAMP NOT NULL DEFAULT now(),
    finished_at   TIMESTAMP,
    error_message TEXT
);

CREATE TABLE audit.dq_check_result (
    id            BIGSERIAL PRIMARY KEY,
    run_id        BIGINT REFERENCES audit.etl_audit_log(run_id),
    check_name    VARCHAR(100) NOT NULL,
    passed        BOOLEAN NOT NULL,
    detail        TEXT,
    checked_at    TIMESTAMP NOT NULL DEFAULT now()
);

-- Seed dim_channel
INSERT INTO dwh.dim_channel(channel) VALUES ('ATM'),('MOBILE'),('INTERNET'),('TELLER');

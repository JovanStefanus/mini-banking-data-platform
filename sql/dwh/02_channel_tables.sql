-- Tabel DWH untuk sumber channel (MySQL mobile banking) dan log aktivitas (MongoDB).
-- Idempotent: dijalankan otomatis untuk volume baru, dan oleh pipeline ETL di setiap run.

CREATE TABLE IF NOT EXISTS dwh.dim_mobile_user (
    id_user       INT PRIMARY KEY,
    id_nasabah    INT NOT NULL,
    device_type   VARCHAR(20) NOT NULL,
    tgl_aktivasi  DATE NOT NULL,
    status        VARCHAR(10) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_mobile_user_nasabah ON dwh.dim_mobile_user(id_nasabah);

CREATE TABLE IF NOT EXISTS dwh.fact_sesi_login (
    id_sesi       BIGINT PRIMARY KEY,
    waktu_key     INT NOT NULL REFERENCES dwh.dim_waktu(waktu_key),
    id_user       INT NOT NULL,
    id_nasabah    INT NOT NULL,          -- business key; sumber tidak mencatat versi nasabah
    waktu_login   TIMESTAMP NOT NULL,
    durasi_detik  INT NOT NULL,
    berhasil      BOOLEAN NOT NULL,
    loaded_at     TIMESTAMP NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_sesi_waktu    ON dwh.fact_sesi_login(waktu_key);
CREATE INDEX IF NOT EXISTS idx_sesi_nasabah  ON dwh.fact_sesi_login(id_nasabah);

-- Alamat IP dari log sengaja TIDAK dimuat (data minimization).
CREATE TABLE IF NOT EXISTS dwh.fact_aktivitas (
    id_log           VARCHAR(24) PRIMARY KEY,   -- _id MongoDB (ObjectId, hex)
    waktu_key        INT NOT NULL REFERENCES dwh.dim_waktu(waktu_key),
    id_nasabah       INT NOT NULL,
    aksi             VARCHAR(30) NOT NULL,
    os               VARCHAR(20),
    versi_app        VARCHAR(10),
    waktu_aktivitas  TIMESTAMP NOT NULL,
    sukses           BOOLEAN NOT NULL,
    loaded_at        TIMESTAMP NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_aktivitas_waktu    ON dwh.fact_aktivitas(waktu_key);
CREATE INDEX IF NOT EXISTS idx_aktivitas_nasabah  ON dwh.fact_aktivitas(id_nasabah);

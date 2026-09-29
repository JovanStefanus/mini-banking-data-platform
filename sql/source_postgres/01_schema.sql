-- Source: Core Banking (data sintetis, bukan data asli)
CREATE TABLE cabang (
    kode_cabang  VARCHAR(5) PRIMARY KEY,
    nama_cabang  VARCHAR(100) NOT NULL,
    kota         VARCHAR(50)  NOT NULL
);

CREATE TABLE produk (
    kode_produk  VARCHAR(5) PRIMARY KEY,
    nama_produk  VARCHAR(100) NOT NULL,
    jenis        VARCHAR(20)  NOT NULL CHECK (jenis IN ('TABUNGAN','GIRO','DEPOSITO','KREDIT'))
);

CREATE TABLE nasabah (
    id_nasabah   SERIAL PRIMARY KEY,
    nik_masked   VARCHAR(16) NOT NULL,          -- sudah dimasking, contoh 3273********0001
    nama         VARCHAR(100) NOT NULL,
    email        VARCHAR(100),
    kota         VARCHAR(50),
    segmen       VARCHAR(20) NOT NULL CHECK (segmen IN ('RITEL','PRIORITAS','BISNIS')),
    tgl_daftar   DATE NOT NULL,
    updated_at   TIMESTAMP NOT NULL DEFAULT now()   -- dipakai untuk incremental load & SCD2
);

CREATE TABLE rekening (
    no_rekening  VARCHAR(12) PRIMARY KEY,
    id_nasabah   INT NOT NULL REFERENCES nasabah(id_nasabah),
    kode_produk  VARCHAR(5) NOT NULL REFERENCES produk(kode_produk),
    kode_cabang  VARCHAR(5) NOT NULL REFERENCES cabang(kode_cabang),
    saldo        NUMERIC(18,2) NOT NULL DEFAULT 0,
    tgl_buka     DATE NOT NULL,
    status       VARCHAR(10) NOT NULL DEFAULT 'AKTIF'
);

CREATE TABLE transaksi (
    id_transaksi     BIGSERIAL PRIMARY KEY,
    no_rekening      VARCHAR(12) NOT NULL REFERENCES rekening(no_rekening),
    jenis_transaksi  VARCHAR(15) NOT NULL CHECK (jenis_transaksi IN ('SETOR','TARIK','TRANSFER_KELUAR','TRANSFER_MASUK','BAYAR')),
    nominal          NUMERIC(18,2) NOT NULL CHECK (nominal > 0),
    channel          VARCHAR(15) NOT NULL CHECK (channel IN ('ATM','MOBILE','INTERNET','TELLER')),
    waktu_transaksi  TIMESTAMP NOT NULL,
    keterangan       VARCHAR(200)
);

CREATE INDEX idx_transaksi_waktu    ON transaksi(waktu_transaksi);
CREATE INDEX idx_transaksi_rekening ON transaksi(no_rekening);
CREATE INDEX idx_nasabah_updated    ON nasabah(updated_at);

-- Tabel staging: salinan mentah dari sumber, di-reload setiap run
CREATE TABLE IF NOT EXISTS staging.cabang (
    kode_cabang VARCHAR(5), nama_cabang VARCHAR(100), kota VARCHAR(50));
CREATE TABLE IF NOT EXISTS staging.produk (
    kode_produk VARCHAR(5), nama_produk VARCHAR(100), jenis VARCHAR(20));
CREATE TABLE IF NOT EXISTS staging.nasabah (
    id_nasabah INT, nama VARCHAR(100), kota VARCHAR(50), segmen VARCHAR(20),
    tgl_daftar DATE, updated_at TIMESTAMP);
CREATE TABLE IF NOT EXISTS staging.rekening (
    no_rekening VARCHAR(12), id_nasabah INT, kode_produk VARCHAR(5), kode_cabang VARCHAR(5));
CREATE TABLE IF NOT EXISTS staging.transaksi (
    id_transaksi BIGINT, no_rekening VARCHAR(12), jenis_transaksi VARCHAR(15),
    nominal NUMERIC(18,2), channel VARCHAR(15), waktu_transaksi TIMESTAMP);

-- Sumber channel (MySQL) dan log (MongoDB)
CREATE TABLE IF NOT EXISTS staging.mobile_user (
    id_user INT, id_nasabah INT, device_type VARCHAR(20), tgl_aktivasi DATE, status VARCHAR(10));
CREATE TABLE IF NOT EXISTS staging.sesi_login (
    id_sesi BIGINT, id_user INT, waktu_login TIMESTAMP, durasi_detik INT, berhasil SMALLINT);
CREATE TABLE IF NOT EXISTS staging.log_aktivitas (
    id_log VARCHAR(24), id_nasabah INT, aksi VARCHAR(30), os VARCHAR(20),
    versi_app VARCHAR(10), waktu_aktivitas TIMESTAMP, sukses BOOLEAN);

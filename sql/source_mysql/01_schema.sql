-- Source: Channel Banking (mobile/internet)
CREATE TABLE mobile_user (
    id_user        INT AUTO_INCREMENT PRIMARY KEY,
    id_nasabah     INT NOT NULL,             -- referensi logis ke core_banking.nasabah
    device_type    VARCHAR(20) NOT NULL,
    tgl_aktivasi   DATE NOT NULL,
    status         VARCHAR(10) NOT NULL DEFAULT 'AKTIF',
    INDEX idx_mobile_nasabah (id_nasabah)
);

CREATE TABLE sesi_login (
    id_sesi      BIGINT AUTO_INCREMENT PRIMARY KEY,
    id_user      INT NOT NULL,
    waktu_login  DATETIME NOT NULL,
    durasi_detik INT NOT NULL,
    berhasil     TINYINT(1) NOT NULL,
    INDEX idx_sesi_user (id_user),
    INDEX idx_sesi_waktu (waktu_login)
);

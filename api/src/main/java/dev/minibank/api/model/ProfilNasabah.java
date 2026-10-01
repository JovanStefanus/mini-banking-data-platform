package dev.minibank.api.model;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

/** Golden record nasabah: gabungan core banking, mobile banking, dan log aktivitas. */
public record ProfilNasabah(
        int idNasabah, String nama, String kota, String segmen, LocalDate tglDaftar,
        boolean punyaMobileBanking, String deviceType, LocalDate tglAktivasiMobile,
        long jumlahTransaksi, BigDecimal totalNominal,
        long jumlahLogin, LocalDateTime loginTerakhir,
        long jumlahAktivitas, long aktivitasGagal, LocalDateTime aktivitasTerakhir) {}

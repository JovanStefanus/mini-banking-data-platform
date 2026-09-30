package dev.minibank.api.model;

import java.math.BigDecimal;
import java.time.Instant;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;

/** Semua bentuk response API dikumpulkan di sini. */
public final class ApiModels {
    private ApiModels() {}

    public record Transaksi(long idTransaksi, LocalDateTime waktuTransaksi, int idNasabah,
                            String namaNasabah, String segmen, String produk, String cabang,
                            String channel, String jenisTransaksi, BigDecimal nominal) {}

    public record Nasabah(int idNasabah, String nama, String kota, String segmen, LocalDate tglDaftar) {}

    /** Satu versi riwayat SCD Type 2. berlakuSampai = null berarti versi yang masih berlaku. */
    public record NasabahVersi(String nama, String kota, String segmen,
                               LocalDateTime berlakuDari, LocalDateTime berlakuSampai, boolean current) {}

    public record RingkasanHarian(LocalDate tanggal, long jumlahTransaksi, BigDecimal totalNominal) {}

    public record PageResponse<T>(int page, int size, long totalElements, int totalPages, List<T> data) {}

    public record ErrorResponse(Instant timestamp, int status, String error, String message) {}
}

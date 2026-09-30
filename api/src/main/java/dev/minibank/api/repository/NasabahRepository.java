package dev.minibank.api.repository;

import dev.minibank.api.model.ApiModels.Nasabah;
import dev.minibank.api.model.ApiModels.NasabahVersi;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

@Repository
public class NasabahRepository {
    private final JdbcTemplate jdbc;

    public NasabahRepository(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    public Optional<Nasabah> findCurrent(int idNasabah) {
        List<Nasabah> rows = jdbc.query("""
                SELECT id_nasabah, nama, kota, segmen, tgl_daftar
                  FROM dwh.dim_nasabah
                 WHERE id_nasabah = ? AND is_current
                """, (rs, i) -> new Nasabah(
                rs.getInt("id_nasabah"),
                rs.getString("nama"),
                rs.getString("kota"),
                rs.getString("segmen"),
                rs.getObject("tgl_daftar", LocalDate.class)), idNasabah);
        return rows.stream().findFirst();
    }

    public List<NasabahVersi> riwayat(int idNasabah) {
        return jdbc.query("""
                SELECT nama, kota, segmen, valid_from, valid_to, is_current
                  FROM dwh.dim_nasabah
                 WHERE id_nasabah = ?
                 ORDER BY valid_from
                """, (rs, i) -> {
            LocalDateTime sampai = rs.getObject("valid_to", LocalDateTime.class);
            if (sampai != null && sampai.getYear() >= 9999) {
                sampai = null;   // penanda "masih berlaku" di DWH
            }
            return new NasabahVersi(
                    rs.getString("nama"),
                    rs.getString("kota"),
                    rs.getString("segmen"),
                    rs.getObject("valid_from", LocalDateTime.class),
                    sampai,
                    rs.getBoolean("is_current"));
        }, idNasabah);
    }
}

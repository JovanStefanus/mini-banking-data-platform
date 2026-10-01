package dev.minibank.api.repository;

import dev.minibank.api.model.ProfilNasabah;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

@Repository
public class ProfilRepository {
    private final JdbcTemplate jdbc;

    public ProfilRepository(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    /** Membaca dari semantic layer, sehingga definisi metrik tidak diduplikasi di API. */
    public Optional<ProfilNasabah> findById(int idNasabah) {
        List<ProfilNasabah> rows = jdbc.query("""
                SELECT id_nasabah, nama, kota, segmen, tgl_daftar,
                       punya_mobile_banking, device_type, tgl_aktivasi_mobile,
                       jumlah_transaksi, total_nominal,
                       jumlah_login, login_terakhir,
                       jumlah_aktivitas, aktivitas_gagal, aktivitas_terakhir
                  FROM semantic.v_nasabah_360
                 WHERE id_nasabah = ?
                """, (rs, i) -> new ProfilNasabah(
                rs.getInt("id_nasabah"),
                rs.getString("nama"),
                rs.getString("kota"),
                rs.getString("segmen"),
                rs.getObject("tgl_daftar", LocalDate.class),
                rs.getBoolean("punya_mobile_banking"),
                rs.getString("device_type"),
                rs.getObject("tgl_aktivasi_mobile", LocalDate.class),
                rs.getLong("jumlah_transaksi"),
                rs.getBigDecimal("total_nominal"),
                rs.getLong("jumlah_login"),
                rs.getObject("login_terakhir", LocalDateTime.class),
                rs.getLong("jumlah_aktivitas"),
                rs.getLong("aktivitas_gagal"),
                rs.getObject("aktivitas_terakhir", LocalDateTime.class)), idNasabah);
        return rows.stream().findFirst();
    }
}

package dev.minibank.api.repository;

import dev.minibank.api.model.ApiModels.RingkasanHarian;
import java.time.LocalDate;
import java.util.List;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

@Repository
public class RingkasanRepository {
    private final JdbcTemplate jdbc;

    public RingkasanRepository(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    public List<RingkasanHarian> harian(LocalDate dari, LocalDate sampai) {
        return jdbc.query("""
                SELECT w.tanggal, COUNT(*) AS jumlah, SUM(f.nominal) AS total
                  FROM dwh.fact_transaksi f
                  JOIN dwh.dim_waktu w ON w.waktu_key = f.waktu_key
                 WHERE w.tanggal BETWEEN ? AND ?
                 GROUP BY w.tanggal
                 ORDER BY w.tanggal
                """, (rs, i) -> new RingkasanHarian(
                rs.getObject("tanggal", LocalDate.class),
                rs.getLong("jumlah"),
                rs.getBigDecimal("total")), dari, sampai);
    }
}

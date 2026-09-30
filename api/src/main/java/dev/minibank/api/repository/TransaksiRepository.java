package dev.minibank.api.repository;

import dev.minibank.api.model.ApiModels.Transaksi;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

@Repository
public class TransaksiRepository {
    private static final String FROM_WHERE = """
            FROM dwh.fact_transaksi f
            JOIN dwh.dim_waktu w    ON w.waktu_key    = f.waktu_key
            JOIN dwh.dim_nasabah n  ON n.nasabah_key  = f.nasabah_key
            JOIN dwh.dim_produk p   ON p.produk_key   = f.produk_key
            JOIN dwh.dim_cabang c   ON c.cabang_key   = f.cabang_key
            JOIN dwh.dim_channel ch ON ch.channel_key = f.channel_key
            WHERE w.tanggal = ?
            """;

    private final JdbcTemplate jdbc;

    public TransaksiRepository(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    public long count(LocalDate tanggal, String channel) {
        List<Object> args = new ArrayList<>();
        args.add(tanggal);
        String sql = "SELECT COUNT(*) " + FROM_WHERE + channelFilter(channel, args);
        Long total = jdbc.queryForObject(sql, Long.class, args.toArray());
        return total == null ? 0 : total;
    }

    public List<Transaksi> find(LocalDate tanggal, String channel, int limit, long offset) {
        List<Object> args = new ArrayList<>();
        args.add(tanggal);
        String sql = """
                SELECT f.id_transaksi, f.waktu_transaksi, n.id_nasabah, n.nama, n.segmen,
                       p.nama_produk, c.nama_cabang, ch.channel, f.jenis_transaksi, f.nominal
                """ + FROM_WHERE + channelFilter(channel, args) + " ORDER BY f.id_transaksi LIMIT ? OFFSET ?";
        args.add(limit);
        args.add(offset);
        return jdbc.query(sql, (rs, i) -> new Transaksi(
                rs.getLong("id_transaksi"),
                rs.getObject("waktu_transaksi", LocalDateTime.class),
                rs.getInt("id_nasabah"),
                rs.getString("nama"),
                rs.getString("segmen"),
                rs.getString("nama_produk"),
                rs.getString("nama_cabang"),
                rs.getString("channel"),
                rs.getString("jenis_transaksi"),
                rs.getBigDecimal("nominal")), args.toArray());
    }

    /** Nilai channel selalu lewat placeholder (?), tidak pernah digabung ke string SQL. */
    private String channelFilter(String channel, List<Object> args) {
        if (channel == null) {
            return "";
        }
        args.add(channel);
        return " AND ch.channel = ?";
    }
}

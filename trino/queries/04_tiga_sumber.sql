SELECT s.segmen_nasabah,
       s.total_nominal,
       m.pengguna_mobile
FROM dwh.semantic.v_segmen_nasabah s
JOIN (SELECT n.segmen, COUNT(DISTINCT mu.id_user) AS pengguna_mobile
      FROM core.public.nasabah n
      JOIN mysql.channel_banking.mobile_user mu ON mu.id_nasabah = n.id_nasabah
      GROUP BY n.segmen) m ON m.segmen = s.segmen_nasabah
ORDER BY s.total_nominal DESC;

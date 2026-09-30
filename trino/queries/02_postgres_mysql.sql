SELECT n.segmen,
       COUNT(DISTINCT n.id_nasabah) AS total_nasabah,
       COUNT(DISTINCT m.id_user)    AS pengguna_mobile,
       ROUND(100.0 * COUNT(DISTINCT m.id_user) / COUNT(DISTINCT n.id_nasabah), 1) AS persen_adopsi
FROM core.public.nasabah n
LEFT JOIN mysql.channel_banking.mobile_user m ON m.id_nasabah = n.id_nasabah
GROUP BY n.segmen
ORDER BY n.segmen;

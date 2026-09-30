SELECT n.kota,
       COUNT(*) AS aktivitas_gagal
FROM mongodb.banking_logs.log_aktivitas l
JOIN core.public.nasabah n ON n.id_nasabah = l.id_nasabah
WHERE l.sukses = false
GROUP BY n.kota
ORDER BY aktivitas_gagal DESC;

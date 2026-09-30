-- Membuat user read-only untuk REST API (prinsip least privilege).
-- Jalankan sebagai superuser DWH, mis. lewat:
--   Get-Content sql\ops\create_api_reader.sql | docker exec -i mbdp_pg_dwh psql -U dwh_user -d dwh -v api_pw=PASSWORD_KAMU
-- Aman dijalankan berulang.

SELECT format('CREATE ROLE api_reader LOGIN PASSWORD %L', :'api_pw')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'api_reader')
\gexec

ALTER ROLE api_reader PASSWORD :'api_pw';

GRANT CONNECT ON DATABASE dwh TO api_reader;
GRANT USAGE ON SCHEMA dwh TO api_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA dwh TO api_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA dwh GRANT SELECT ON TABLES TO api_reader;
-- Sengaja TIDAK ada akses ke schema staging dan audit.

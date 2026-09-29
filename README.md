# Mini Banking Data Platform

Simulasi platform data ala perbankan: multi-source → ETL → Data Warehouse (star schema) → API & dashboard.
**Semua data sintetis** (Faker), tidak ada data nasabah asli.

## Status
- [x] Fase 1: source DB (PostgreSQL, MySQL, MongoDB), star schema DWH, generator data
- [ ] Fase 2: ETL (Airflow), SCD2, audit log, data quality
- [ ] Fase 3: REST API Java Spring Boot
- [ ] Fase 4: Trino (data virtualization), semantic layer, dashboard
- [ ] Fase 5: Oracle/SQL Server, Kubernetes, CI

## Cara menjalankan
```bash
cp .env.example .env            # lalu ganti password
docker compose up -d
cd data_generator
pip install -r requirements.txt
set -a; source ../.env; set +a  # (Linux/Mac) muat password ke environment
python generate.py --nasabah 5000 --transaksi 200000
```

## Port
| Service | Port |
|---|---|
| PostgreSQL core banking | 15432 |
| PostgreSQL DWH | 5433 |
| MySQL channel | 3307 |
| MongoDB | 27017 |

## Model data (star schema)
`fact_transaksi` dikelilingi `dim_waktu`, `dim_nasabah` (SCD2), `dim_produk`, `dim_cabang`, `dim_channel`.

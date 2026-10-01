"""Koneksi database. Kredensial dibaca dari environment variable (.env), tidak ditulis di kode."""
import os

import psycopg2


def _env(key, default):
    return os.environ.get(key, default)


def source_conn():
    """Koneksi ke core banking. Read-only: ETL tidak boleh mengubah sumber."""
    conn = psycopg2.connect(
        host=_env("PG_CORE_HOST", "127.0.0.1"), port=_env("PG_CORE_PORT", "15432"),
        dbname="core_banking", user="core_user", password=_env("PG_CORE_PASSWORD", ""))
    conn.set_session(readonly=True)
    return conn


def dwh_conn(autocommit=False):
    conn = psycopg2.connect(
        host=_env("PG_DWH_HOST", "127.0.0.1"), port=_env("PG_DWH_PORT", "5433"),
        dbname="dwh", user="dwh_user", password=_env("PG_DWH_PASSWORD", ""))
    conn.autocommit = autocommit
    return conn


def mysql_conn():
    """Koneksi ke channel banking (MySQL). Sesi dibuat read-only."""
    import mysql.connector
    conn = mysql.connector.connect(
        host=_env("MYSQL_HOST", "127.0.0.1"), port=int(_env("MYSQL_PORT", "3307")),
        database="channel_banking", user="channel_user", password=_env("MYSQL_PASSWORD", ""))
    cur = conn.cursor()
    cur.execute("SET SESSION TRANSACTION READ ONLY")
    cur.close()
    return conn


def mongo_client():
    """Koneksi ke MongoDB (log aktivitas). ETL hanya membaca."""
    from pymongo import MongoClient
    return MongoClient(
        host=_env("MONGO_HOST", "127.0.0.1"), port=int(_env("MONGO_PORT", "27017")),
        username="mongo_user", password=_env("MONGO_PASSWORD", ""), authSource="admin")

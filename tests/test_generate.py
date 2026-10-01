"""Menjaga generator data tetap sejalan dengan skema SQL (CHECK constraint)."""
import re
from pathlib import Path

import generate

SCHEMA = (Path(__file__).resolve().parent.parent / "sql" / "source_postgres" / "01_schema.sql").read_text()


def _nilai_diizinkan(kolom):
    cocok = re.search(rf"CHECK \(\s*{kolom} IN \(([^)]*)\)\s*\)", SCHEMA)
    assert cocok, f"CHECK constraint untuk kolom {kolom} tidak ditemukan di skema"
    return set(re.findall(r"'([^']+)'", cocok.group(1)))


def test_nik_dimasking():
    for _ in range(50):
        assert re.fullmatch(r"\d{4}\*{8}\d{4}", generate.masked_nik())


def test_channel_sesuai_skema():
    assert set(generate.CHANNEL) == _nilai_diizinkan("channel")


def test_jenis_transaksi_sesuai_skema():
    assert set(generate.JENIS_TRX) == _nilai_diizinkan("jenis_transaksi")


def test_segmen_sesuai_skema():
    assert set(generate.SEGMEN) == _nilai_diizinkan("segmen")


def test_jenis_produk_sesuai_skema():
    assert {jenis for _, _, jenis in generate.PRODUK} <= _nilai_diizinkan("jenis")


def test_kode_cabang_dan_produk_unik():
    assert len({kode for kode, _, _ in generate.CABANG}) == len(generate.CABANG)
    assert len({kode for kode, _, _ in generate.PRODUK}) == len(generate.PRODUK)

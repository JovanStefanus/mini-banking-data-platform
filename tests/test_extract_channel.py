"""Unit test extract MongoDB tanpa database: koneksi diganti objek tiruan (mock)."""
from datetime import datetime
from unittest.mock import MagicMock, patch

from bson import ObjectId

from etl import extract_channel


def _mongo_dengan(docs):
    col = MagicMock()
    col.find.return_value.sort.return_value.batch_size.return_value = docs
    db = MagicMock()
    db.__getitem__.return_value = col
    mongo = MagicMock()
    mongo.__getitem__.return_value = db
    return mongo, col


def _dokumen(**ubah):
    dasar = {"_id": ObjectId(), "id_nasabah": 7, "aksi": "LOGIN", "ip": "10.1.2.3",
             "perangkat": {"os": "ANDROID", "versi_app": "9.1"},
             "waktu": datetime(2026, 9, 1, 10, 0), "sukses": True}
    dasar.update(ubah)
    return dasar


def _jalankan(docs, last_id=None):
    """Jalankan extract dan tangkap baris yang dikirim ke staging."""
    mongo, col = _mongo_dengan(docs)
    dwh = MagicMock()
    terkirim = []

    def tangkap(cursor, sql, rows, page_size=None):
        terkirim.extend(rows)      # salin dulu, karena list asli dikosongkan setelah flush

    with patch.object(extract_channel, "execute_values", side_effect=tangkap):
        hasil = extract_channel.extract_mongo_log(mongo, dwh, last_id)
    return hasil, terkirim, col


def test_dokumen_valid_dimuat():
    (read, loaded, rejected), baris, _ = _jalankan([_dokumen()])
    assert (read, loaded, rejected) == (1, 1, 0)
    assert baris[0][1:3] == (7, "LOGIN")


def test_alamat_ip_tidak_ikut_dimuat():
    _, baris, _ = _jalankan([_dokumen(ip="10.1.2.3")])
    assert all("10.1.2.3" not in kolom for kolom in map(str, baris[0]))


def test_dokumen_tidak_lengkap_ditolak():
    docs = [_dokumen(), _dokumen(id_nasabah=None), _dokumen(waktu=None), _dokumen(aksi="")]
    (read, loaded, rejected), baris, _ = _jalankan(docs)
    assert (read, loaded, rejected) == (4, 1, 3)
    assert len(baris) == 1


def test_perangkat_kosong_tidak_menyebabkan_error():
    _, baris, _ = _jalankan([_dokumen(perangkat=None)])
    assert baris[0][3] is None and baris[0][4] is None


def test_watermark_dipakai_sebagai_filter_id():
    terakhir = ObjectId()
    _, _, col = _jalankan([], last_id=str(terakhir))
    col.find.assert_called_once_with({"_id": {"$gt": terakhir}})


def test_tanpa_watermark_semua_dokumen_diambil():
    _, _, col = _jalankan([])
    col.find.assert_called_once_with({})

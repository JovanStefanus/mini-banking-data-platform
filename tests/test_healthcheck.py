from contextlib import ExitStack
from unittest.mock import MagicMock, patch

from etl import healthcheck

SUMBER = ("source_conn", "dwh_conn", "mysql_conn", "mongo_client")


def test_semua_sumber_sehat_menghasilkan_kode_nol():
    with ExitStack() as stack:
        for nama in SUMBER:
            stack.enter_context(patch.object(healthcheck, nama, return_value=MagicMock()))
        assert healthcheck.main() == 0


def test_satu_sumber_gagal_menghasilkan_kode_satu():
    with ExitStack() as stack:
        for nama in SUMBER:
            if nama == "mongo_client":
                stack.enter_context(patch.object(healthcheck, nama, side_effect=Exception("koneksi ditolak")))
            else:
                stack.enter_context(patch.object(healthcheck, nama, return_value=MagicMock()))
        assert healthcheck.main() == 1


def test_sumber_yang_gagal_tidak_menghentikan_pemeriksaan_lainnya(capsys):
    with ExitStack() as stack:
        for nama in SUMBER:
            if nama == "source_conn":
                stack.enter_context(patch.object(healthcheck, nama, side_effect=Exception("mati")))
            else:
                stack.enter_context(patch.object(healthcheck, nama, return_value=MagicMock()))
        healthcheck.main()
    keluaran = capsys.readouterr().out
    assert "[GAGAL]  postgres_core" in keluaran
    assert "[OK]     mongo_logs" in keluaran

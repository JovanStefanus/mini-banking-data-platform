from etl import transform_load as tl


def test_rentang_dim_waktu_mencakup_2020_sampai_2030():
    hari = (tl.END_DATE - tl.START_DATE).days + 1
    assert hari == 4018          # sama dengan jumlah baris dim_waktu hasil pipeline
    assert tl.START_DATE.year == 2020
    assert tl.END_DATE.year == 2030

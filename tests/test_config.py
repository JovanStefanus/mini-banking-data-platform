from etl import config


def test_env_memakai_default_kalau_variabel_tidak_ada(monkeypatch):
    monkeypatch.delenv("VARIABEL_TIDAK_ADA", raising=False)
    assert config._env("VARIABEL_TIDAK_ADA", "nilai-default") == "nilai-default"


def test_env_memakai_nilai_environment_kalau_ada(monkeypatch):
    monkeypatch.setenv("PG_DWH_PORT", "6543")
    assert config._env("PG_DWH_PORT", "5433") == "6543"

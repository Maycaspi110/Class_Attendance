import importlib


def test_the_production_entry_point_creates_the_app(monkeypatch):
    monkeypatch.setenv("LECTURER_PASSWORD", "x")
    monkeypatch.setenv("CODE_SECRET", "y")
    monkeypatch.delenv("PUBLIC_URL", raising=False)
    monkeypatch.setenv("RENDER_EXTERNAL_URL", "https://example.onrender.com")
    import wsgi

    wsgi = importlib.reload(wsgi)
    assert wsgi.app.config["PUBLIC_URL"] == "https://example.onrender.com"
    assert wsgi.app.test_client().get("/checkin").status_code == 200


import pytest  # noqa: E402

from app import create_app  # noqa: E402


@pytest.mark.parametrize("flag", [{"REQUIRE_SECRETS": "1"}, {"RENDER": "true"}])
def test_a_real_server_refuses_to_start_without_its_secrets(monkeypatch, flag):
    monkeypatch.delenv("LECTURER_PASSWORD", raising=False)
    monkeypatch.delenv("CODE_SECRET", raising=False)
    for name, value in flag.items():
        monkeypatch.setenv(name, value)
    with pytest.raises(RuntimeError) as error:
        create_app()
    assert "LECTURER_PASSWORD" in str(error.value) and "CODE_SECRET" in str(error.value)


def test_a_real_server_starts_when_the_secrets_are_set(monkeypatch):
    monkeypatch.setenv("REQUIRE_SECRETS", "1")
    monkeypatch.setenv("LECTURER_PASSWORD", "a-long-password")
    monkeypatch.setenv("CODE_SECRET", "a-long-secret")
    assert create_app().test_client().get("/checkin").status_code == 200


def test_on_your_own_computer_the_fallbacks_still_work(monkeypatch):
    for name in ("REQUIRE_SECRETS", "RENDER", "LECTURER_PASSWORD", "CODE_SECRET"):
        monkeypatch.delenv(name, raising=False)
    assert create_app().test_client().get("/checkin").status_code == 200

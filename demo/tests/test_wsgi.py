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

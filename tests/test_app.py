import os
import importlib
import tempfile

import pytest

from app import app, PROJECTS_DIR


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Test client with an isolated projects directory."""
    monkeypatch.setattr("app.PROJECTS_DIR", str(tmp_path))
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------

def test_index_returns_200(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"VAULT 111" in resp.data


# ---------------------------------------------------------------------------
# POST /save — happy path
# ---------------------------------------------------------------------------

def test_save_creates_file(client, tmp_path, monkeypatch):
    monkeypatch.setattr("app.PROJECTS_DIR", str(tmp_path))
    resp = client.post("/save", data={"name": "my-idea", "content": "# Hello"})
    assert resp.status_code == 200
    assert (tmp_path / "my-idea.md").exists()
    assert (tmp_path / "my-idea.md").read_text() == "# Hello"


def test_save_sanitizes_name(client, tmp_path, monkeypatch):
    monkeypatch.setattr("app.PROJECTS_DIR", str(tmp_path))
    resp = client.post("/save", data={"name": "  My Idea  ", "content": "x"})
    assert resp.status_code == 200
    assert (tmp_path / "my-idea.md").exists()


def test_save_strips_null_bytes(client, tmp_path, monkeypatch):
    monkeypatch.setattr("app.PROJECTS_DIR", str(tmp_path))
    resp = client.post("/save", data={"name": "clean", "content": "hello\x00world"})
    assert resp.status_code == 200
    assert (tmp_path / "clean.md").read_text() == "helloworld"


# ---------------------------------------------------------------------------
# POST /save — validation errors
# ---------------------------------------------------------------------------

def test_save_rejects_empty_name(client):
    resp = client.post("/save", data={"name": "", "content": "x"})
    assert resp.status_code == 400
    assert b"required" in resp.data.lower()


def test_save_rejects_long_name(client):
    long_name = "a" * 65
    resp = client.post("/save", data={"name": long_name, "content": "x"})
    assert resp.status_code == 400


def test_save_rejects_invalid_characters(client):
    for bad in ["../etc/passwd", "foo/bar", "foo\\bar", "foo!bar"]:
        resp = client.post("/save", data={"name": bad, "content": "x"})
        assert resp.status_code == 400, f"Expected 400 for name={bad!r}"


def test_save_rejects_oversized_content(client):
    big = "x" * (100 * 1024 + 1)
    resp = client.post("/save", data={"name": "bigfile", "content": big})
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# POST /save — conflict
# ---------------------------------------------------------------------------

def test_save_returns_409_on_duplicate(client, tmp_path, monkeypatch):
    monkeypatch.setattr("app.PROJECTS_DIR", str(tmp_path))
    client.post("/save", data={"name": "dup", "content": "first"})
    resp = client.post("/save", data={"name": "dup", "content": "second"})
    assert resp.status_code == 409
    # Original file must be untouched
    assert (tmp_path / "dup.md").read_text() == "first"


# ---------------------------------------------------------------------------
# GET /list
# ---------------------------------------------------------------------------

def test_list_shows_files(client, tmp_path, monkeypatch):
    monkeypatch.setattr("app.PROJECTS_DIR", str(tmp_path))
    (tmp_path / "alpha.md").write_text("a")
    (tmp_path / "beta.md").write_text("b")
    resp = client.get("/list")
    assert resp.status_code == 200
    assert b"alpha.md" in resp.data
    assert b"beta.md" in resp.data


def test_list_empty(client, tmp_path, monkeypatch):
    monkeypatch.setattr("app.PROJECTS_DIR", str(tmp_path))
    resp = client.get("/list")
    assert resp.status_code == 200
    assert b"No ideas" in resp.data


# ---------------------------------------------------------------------------
# VAULT_PROJECTS_DIR env var
# ---------------------------------------------------------------------------

def test_projects_dir_respects_env_var(tmp_path, monkeypatch):
    """VAULT_PROJECTS_DIR env var overrides the built-in default."""
    monkeypatch.setenv("VAULT_PROJECTS_DIR", str(tmp_path))
    import app as app_module
    importlib.reload(app_module)
    try:
        assert app_module.PROJECTS_DIR == str(tmp_path)
    finally:
        # Always restore the module to its original state so other tests are unaffected.
        monkeypatch.delenv("VAULT_PROJECTS_DIR", raising=False)
        importlib.reload(app_module)

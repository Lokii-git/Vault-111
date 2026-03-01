# Vault-111

A lightweight, self-hosted web app for storing project ideas and notes as Markdown files. Built with a retro terminal aesthetic and designed to run on a local machine or private server (e.g. Kali Linux).

## Features

- Save named project ideas / specs as `.md` files
- Browse a list of all saved ideas
- Enforces safe filenames (lowercase, hyphens, underscores only — max 64 chars)
- Strips null bytes; rejects content over 100 KB
- Retro green-on-black terminal UI

## Requirements

- Python 3.10+
- pip

All Python dependencies are listed in `requirements.txt` (Flask ≥ 3.0, Gunicorn ≥ 21.2).

## Quick Start (Kali / Debian)

Run the provided installer, which sets up a virtual environment, installs dependencies, and registers a systemd service:

```bash
chmod +x install.sh
sudo ./install.sh
```

After installation the app is available at **http://127.0.0.1:5111**.

### Service management

```bash
sudo systemctl start  vault-111   # start
sudo systemctl stop   vault-111   # stop
sudo systemctl status vault-111   # check status
sudo systemctl enable vault-111   # start on boot (already done by installer)
```

## Manual Setup (without the installer)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run with Gunicorn (production)
gunicorn -c gunicorn.conf.py app:app

# Or run the dev server (not for production)
python app.py
```

## Project structure

```
Vault-111/
├── app.py              # Flask application
├── gunicorn.conf.py    # Gunicorn configuration
├── requirements.txt    # Python dependencies
├── templates/
│   ├── index.html      # Save-idea form
│   └── list.html       # Saved-ideas list
├── projects/           # Created automatically; stores .md files
├── install.sh          # Kali / Debian installer
└── tests/
    └── test_app.py     # pytest test suite
```

## Configuration

| Environment variable | Default | Description |
|---|---|---|
| `VAULT_PROJECTS_DIR` | `<app-dir>/projects` | Absolute path to the directory where `.md` idea files are stored. |

Set it before starting the app:

```bash
# manual / dev
export VAULT_PROJECTS_DIR=/mnt/data/vault-ideas
gunicorn -c gunicorn.conf.py app:app
```

When using the systemd service (installed by `install.sh`), edit the `Environment=` line in the unit file and reload:

```bash
sudo systemctl edit --full vault-111   # find and update VAULT_PROJECTS_DIR=
sudo systemctl daemon-reload
sudo systemctl restart vault-111
```

## Running tests

```bash
pip install pytest
pytest tests/
```

## License

MIT — see [LICENSE](LICENSE).

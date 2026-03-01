#!/usr/bin/env bash
# install.sh — Vault-111 installer for Kali Linux / Debian
# Usage: sudo ./install.sh
set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration — edit these if you want to change the install location or
# the user that runs the service.
# ---------------------------------------------------------------------------
INSTALL_DIR="/opt/vault-111"
SERVICE_USER="vault111"
SERVICE_FILE="/etc/systemd/system/vault-111.service"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
info()  { echo "[*] $*"; }
ok()    { echo "[+] $*"; }
die()   { echo "[-] $*" >&2; exit 1; }

[[ $EUID -eq 0 ]] || die "Please run as root: sudo ./install.sh"

# ---------------------------------------------------------------------------
# 1. System dependencies
# ---------------------------------------------------------------------------
info "Updating package lists and installing dependencies..."
apt-get update -qq
apt-get install -y -qq python3 python3-pip python3-venv

# ---------------------------------------------------------------------------
# 2. Create a dedicated service user (no login shell)
# ---------------------------------------------------------------------------
if ! id -u "$SERVICE_USER" &>/dev/null; then
    info "Creating service user '$SERVICE_USER'..."
    useradd --system --no-create-home --shell /usr/sbin/nologin "$SERVICE_USER"
fi

# ---------------------------------------------------------------------------
# 3. Copy application files
# ---------------------------------------------------------------------------
info "Installing application to $INSTALL_DIR ..."
mkdir -p "$INSTALL_DIR"

# Copy everything except the .git directory and any existing venv
rsync -a --exclude='.git' --exclude='.venv' \
    "$(dirname "$(realpath "$0")")/" "$INSTALL_DIR/"

# Ensure the projects storage directory exists and is owned by the service user
mkdir -p "$INSTALL_DIR/projects"
chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
chmod 750 "$INSTALL_DIR"

# ---------------------------------------------------------------------------
# 4. Python virtual environment + dependencies
# ---------------------------------------------------------------------------
info "Creating Python virtual environment..."
python3 -m venv "$INSTALL_DIR/.venv"
"$INSTALL_DIR/.venv/bin/pip" install --quiet --upgrade pip
"$INSTALL_DIR/.venv/bin/pip" install --quiet -r "$INSTALL_DIR/requirements.txt"

# ---------------------------------------------------------------------------
# 5. systemd service
# ---------------------------------------------------------------------------
info "Writing systemd service to $SERVICE_FILE ..."
cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Vault-111 — Secure Idea Storage
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/.venv/bin/gunicorn -c $INSTALL_DIR/gunicorn.conf.py app:app
Restart=on-failure
RestartSec=5
# Hardening
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

# ---------------------------------------------------------------------------
# 6. Enable and start the service
# ---------------------------------------------------------------------------
info "Reloading systemd and enabling vault-111..."
systemctl daemon-reload
systemctl enable vault-111
systemctl restart vault-111

ok "Vault-111 is running at http://127.0.0.1:5111"
ok "Manage with: sudo systemctl {start|stop|status|restart} vault-111"

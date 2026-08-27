#!/usr/bin/env bash
# One-time setup for HTBG Tracker on a fresh Ubuntu 24.04 VPS.
#
#   sudo bash bootstrap.sh <git-repo-url> <domain>
#   e.g. sudo bash bootstrap.sh git@github.com:you/hattrick_bg_scout.git htbg.duckdns.org
#
# Installs: python venv + app under /opt/htbg (user "htbg"), systemd service,
# Caddy with automatic HTTPS, daily SQLite backup, passwordless restart for CI.
set -euo pipefail

REPO_URL="${1:?usage: bootstrap.sh <git-repo-url> <domain>}"
DOMAIN="${2:?usage: bootstrap.sh <git-repo-url> <domain>}"
APP_DIR=/opt/htbg

apt-get update
apt-get install -y python3-venv python3-pip git sqlite3 curl \
  debian-keyring debian-archive-keyring apt-transport-https

if ! command -v caddy >/dev/null; then
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' \
    | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' \
    > /etc/apt/sources.list.d/caddy-stable.list
  apt-get update && apt-get install -y caddy
fi

id -u htbg &>/dev/null || useradd --system --create-home --shell /bin/bash htbg

if [ ! -d "$APP_DIR/.git" ]; then
  git clone "$REPO_URL" "$APP_DIR"
fi
chown -R htbg:htbg "$APP_DIR"
sudo -u htbg python3 -m venv "$APP_DIR/.venv"
sudo -u htbg "$APP_DIR/.venv/bin/pip" install -q -r "$APP_DIR/requirements.txt"

if [ ! -f "$APP_DIR/.env" ]; then
  SECRET=$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')
  cat > "$APP_DIR/.env" <<EOF
CHPP_MOCK=0
CHPP_CONSUMER_KEY=
CHPP_CONSUMER_SECRET=
SECRET_KEY=$SECRET
DATABASE_URL=sqlite:///$APP_DIR/scoutbridge.db
BASE_URL=https://$DOMAIN
EOF
  chown htbg:htbg "$APP_DIR/.env"
  chmod 600 "$APP_DIR/.env"
  echo ">> NB: fill in the CHPP keys in $APP_DIR/.env"
fi

install -m 644 "$APP_DIR/deploy/htbg.service" /etc/systemd/system/htbg.service
sed "s/__DOMAIN__/$DOMAIN/" "$APP_DIR/deploy/Caddyfile" > /etc/caddy/Caddyfile

# CI deploys as user htbg and may only restart the app service.
echo 'htbg ALL=(root) NOPASSWD: /usr/bin/systemctl restart htbg' \
  > /etc/sudoers.d/htbg-deploy
chmod 440 /etc/sudoers.d/htbg-deploy

chmod +x "$APP_DIR/deploy/backup.sh" "$APP_DIR/deploy/remote-deploy.sh"
echo '10 4 * * * htbg /opt/htbg/deploy/backup.sh' > /etc/cron.d/htbg-backup

systemctl daemon-reload
systemctl enable --now htbg
systemctl enable --now caddy
systemctl reload caddy

echo "Done. App should be live at https://$DOMAIN once DNS points here."

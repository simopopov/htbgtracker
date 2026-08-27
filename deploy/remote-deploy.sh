#!/usr/bin/env bash
# Executed on the server by the GitHub Actions deploy job (as user htbg).
set -euo pipefail
cd /opt/htbg

git fetch origin main
git reset --hard origin/main
.venv/bin/pip install -q -r requirements.txt
sudo systemctl restart htbg

sleep 2
curl -fsS -o /dev/null http://127.0.0.1:8000/login
echo "deploy OK: $(git rev-parse --short HEAD)"

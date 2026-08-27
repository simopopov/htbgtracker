# Deployment (Hetzner VPS + GitHub Actions CI/CD)

Push to `main` → tests run → on green, GitHub Actions deploys to the server
over SSH and restarts the service. No manual SSH after the one-time setup.

## One-time setup

### 1. GitHub repo

```bash
git push -u origin main       # after creating the repo on GitHub
```

### 2. Server (Hetzner CX23, Ubuntu 24.04)

As root on the fresh server:

```bash
# Give the server read access to the repo (skip if the repo is public):
sudo -u htbg ssh-keygen -t ed25519 -N '' -f /home/htbg/.ssh/id_ed25519 || true
cat /home/htbg/.ssh/id_ed25519.pub
#   → add as a read-only Deploy Key: GitHub repo → Settings → Deploy keys
# (the htbg user is created by bootstrap; run the keygen after step below
#  errors on clone, or pre-create the user: useradd -m htbg)

curl -fsSL https://raw.githubusercontent.com/<you>/<repo>/main/deploy/bootstrap.sh -o bootstrap.sh
sudo bash bootstrap.sh git@github.com:<you>/<repo>.git <domain>
```

`<domain>`: a real domain or a free DuckDNS subdomain pointed at the server
IP. Caddy fetches the HTTPS certificate automatically.

Then fill in the CHPP keys:

```bash
sudo nano /opt/htbg/.env    # CHPP_CONSUMER_KEY / CHPP_CONSUMER_SECRET
sudo systemctl restart htbg
```

### 3. CI deploy key + GitHub secrets

```bash
# On your machine — a key used ONLY by GitHub Actions to reach the server:
ssh-keygen -t ed25519 -N '' -f htbg-deploy-key
ssh-copy-id -i htbg-deploy-key.pub htbg@<server-ip>   # or append to
#   /home/htbg/.ssh/authorized_keys manually
```

GitHub repo → Settings → Secrets and variables → Actions:

| Secret | Value |
|---|---|
| `SSH_HOST` | the server IP (or domain) |
| `SSH_KEY` | contents of the **private** file `htbg-deploy-key` |

Delete the local key files after adding the secret.

### 4. CHPP settings

In your CHPP product settings on hattrick.org, make sure the OAuth callback
matches `https://<domain>/auth/chpp/callback` (the app sends it at request-
token time from `BASE_URL`).

## Day-to-day

- `git push` to `main` → tests → deploy → health check (`/login`).
- Pull requests run tests only, no deploy.
- DB migrations run automatically at app startup (`init_db`).
- Backups: daily 04:10 to `/opt/htbg/backups/`, 14-day rotation. Copy them
  off-server occasionally: `scp htbg@<server>:/opt/htbg/backups/*.gz .`

## Useful commands on the server

```bash
systemctl status htbg           # is it running
journalctl -u htbg -n 100 -f    # app logs
systemctl reload caddy          # after editing /etc/caddy/Caddyfile
```

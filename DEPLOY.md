# Deployment — Vercel + Supabase (free tiers)

Push to `main` → GitHub Actions runs the tests, Vercel's git integration
builds and deploys. Postgres lives in Supabase. Total cost: 0.

## One-time setup

### 1. Supabase

1. supabase.com → New project (region: EU/Frankfurt). Save the DB password.
2. Project → Connect → copy two connection strings:
   - **Transaction pooler** (port 6543) → the app's `DATABASE_URL`
   - **Session pooler** (port 5432) → GitHub secret `SUPABASE_DB_URL`
     (for backups; the direct host is IPv6-only and won't work from CI)

Tables are created automatically on the first cold start (`init_db`).

### 2. Vercel

1. Push the repo to GitHub, then vercel.com → Add New Project → import it.
   The included `vercel.json` + `api/index.py` make FastAPI work as-is.
2. Project → Settings → Environment Variables:

   | Variable | Value |
   |---|---|
   | `DATABASE_URL` | the **transaction pooler** string from Supabase |
   | `SECRET_KEY` | long random string (`python3 -c "import secrets; print(secrets.token_urlsafe(48))"`) |
   | `CHPP_MOCK` | `0` |
   | `CHPP_CONSUMER_KEY` | from the CHPP product page |
   | `CHPP_CONSUMER_SECRET` | from the CHPP product page |
   | `BASE_URL` | `https://<project>.vercel.app` (or your domain) |

3. Deploy. Every later `git push` deploys automatically; PRs get preview
   deployments (they share the same DB — don't run destructive experiments
   from previews).

### 3. GitHub Actions plumbing

- Repo → Settings → Secrets and variables → Actions:
  - **Variable** `APP_URL` = `https://<project>.vercel.app`
    (used by `keepalive.yml` — pings `/healthz` every 3 days so the free
    Supabase project is never paused for inactivity)
  - **Secret** `SUPABASE_DB_URL` = the session-pooler string
    (used by `backup.yml` — weekly `pg_dump`, stored as a workflow artifact
    for 90 days; Supabase free has no automated backups of its own)

### 4. CHPP settings

Make sure the OAuth callback on the CHPP product page allows
`https://<project>.vercel.app/auth/chpp/callback` (the app derives it from
`BASE_URL`). The first user to log in on the fresh database becomes head
coach.

## Notes

- Local development is unchanged: SQLite + mock mode (`CHPP_MOCK=1`).
- The SQLite column migrations don't apply to Postgres; a fresh Supabase DB
  gets the full schema from `create_all`. Future schema changes on a live
  Postgres DB need an `ALTER TABLE` run in the Supabase SQL editor (or a
  proper migration tool if this grows).
- Restoring a backup: `gunzip -c backup-YYYYMMDD.sql.gz | psql "<session-pooler-url>"`.
- If the DB was still paused for any reason: Supabase dashboard → Restore.

## Alternative: self-hosted VPS

The `deploy/` folder keeps a complete Hetzner/Ubuntu setup (systemd + Caddy
+ SSH deploy + daily SQLite backups) in case the project ever outgrows the
free tiers or wants to leave them. See the scripts' headers for usage.

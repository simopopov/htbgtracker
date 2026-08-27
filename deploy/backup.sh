#!/usr/bin/env bash
# Daily SQLite backup with 14-day rotation (run from cron as user htbg).
set -euo pipefail
APP_DIR=/opt/htbg
BACKUP_DIR=$APP_DIR/backups
mkdir -p "$BACKUP_DIR"

STAMP=$(date +%Y%m%d)
# .backup takes a consistent snapshot even while the app is writing.
sqlite3 "$APP_DIR/scoutbridge.db" ".backup '$BACKUP_DIR/scoutbridge-$STAMP.db'"
gzip -f "$BACKUP_DIR/scoutbridge-$STAMP.db"

ls -1t "$BACKUP_DIR"/scoutbridge-*.db.gz | tail -n +15 | xargs -r rm

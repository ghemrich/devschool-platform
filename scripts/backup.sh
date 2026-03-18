#!/bin/bash
set -euo pipefail

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/openschool/backups"
mkdir -p "$BACKUP_DIR"

docker compose -f /opt/openschool/docker-compose.prod.yml exec -T db \
  pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_DIR/db_$TIMESTAMP.sql.gz"

# Remove backups older than 30 days
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: db_$TIMESTAMP.sql.gz"

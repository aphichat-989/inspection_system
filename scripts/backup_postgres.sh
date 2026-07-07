#!/bin/sh
set -eu

ENV_FILE="${ENV_FILE:-.env.production}"

if [ ! -f "$ENV_FILE" ]; then
  echo "Missing env file: $ENV_FILE" >&2
  exit 1
fi

set -a
. "$ENV_FILE"
set +a

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.production.yml}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"

if [ ! -f "$COMPOSE_FILE" ]; then
  echo "Missing compose file: $COMPOSE_FILE" >&2
  exit 1
fi

mkdir -p "$BACKUP_DIR"

timestamp="$(date +%Y%m%d_%H%M%S)"
backup_file="$BACKUP_DIR/${DB_NAME}_${timestamp}.dump"

echo "Creating PostgreSQL backup: $backup_file"
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T db \
  pg_dump -U "$DB_USER" -d "$DB_NAME" -Fc > "$backup_file"

echo "Cleaning backups older than $BACKUP_RETENTION_DAYS days in $BACKUP_DIR"
find "$BACKUP_DIR" -type f -name "${DB_NAME}_*.dump" -mtime +"$BACKUP_RETENTION_DAYS" -delete

echo "Backup completed: $backup_file"

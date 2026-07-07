#!/bin/sh
set -eu

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.production.yml}"
ENV_FILE="${ENV_FILE:-.env.production}"

if [ ! -f "$ENV_FILE" ]; then
  echo "Environment file not found: $ENV_FILE" >&2
  exit 1
fi

set -a
. "$ENV_FILE"
set +a

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.production.yml}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"

: "${DB_NAME:?DB_NAME is required}"
: "${DB_USER:?DB_USER is required}"

mkdir -p "$BACKUP_DIR"

DATE="$(date +%Y%m%d_%H%M%S)"
BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_${DATE}.dump"

docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T db \
  pg_dump -U "$DB_USER" -d "$DB_NAME" -Fc > "$BACKUP_FILE"

find "$BACKUP_DIR" -type f -name "${DB_NAME}_*.dump" -mtime +"$BACKUP_RETENTION_DAYS" -delete

echo "Backup created: $BACKUP_FILE"

#!/bin/sh
set -eu

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.production.yml}"
ENV_FILE="${ENV_FILE:-.env.production}"

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 path/to/backup.dump" >&2
  exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$ENV_FILE" ]; then
  echo "Environment file not found: $ENV_FILE" >&2
  exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
  echo "Backup file not found: $BACKUP_FILE" >&2
  exit 1
fi

set -a
. "$ENV_FILE"
set +a

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.production.yml}"

: "${DB_NAME:?DB_NAME is required}"
: "${DB_USER:?DB_USER is required}"

docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" stop web

docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T db \
  pg_restore -U "$DB_USER" -d "$DB_NAME" --clean --if-exists < "$BACKUP_FILE"

docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" run --rm web \
  python manage.py migrate --noinput

docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d web

echo "Restore completed from: $BACKUP_FILE"

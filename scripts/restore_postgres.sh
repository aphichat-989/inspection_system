#!/bin/sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 path/to/backup.dump" >&2
  exit 1
fi

backup_file="$1"
ENV_FILE="${ENV_FILE:-.env.production}"

if [ ! -f "$backup_file" ]; then
  echo "Backup file not found: $backup_file" >&2
  exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
  echo "Missing env file: $ENV_FILE" >&2
  exit 1
fi

set -a
. "$ENV_FILE"
set +a

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.production.yml}"

if [ ! -f "$COMPOSE_FILE" ]; then
  echo "Missing compose file: $COMPOSE_FILE" >&2
  exit 1
fi

compose() {
  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" "$@"
}

echo "Stopping web service before restore..."
compose stop web

echo "Terminating active database sessions..."
compose exec -T db psql -U "$DB_USER" -d postgres -v ON_ERROR_STOP=1 -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();"

echo "Restoring database from: $backup_file"
compose exec -T db pg_restore \
  -U "$DB_USER" \
  -d "$DB_NAME" \
  --clean \
  --if-exists \
  --no-owner \
  --no-acl < "$backup_file"

echo "Running migrations after restore..."
compose run --rm web python manage.py migrate --noinput

echo "Starting web service..."
compose up -d web

echo "Restore completed."

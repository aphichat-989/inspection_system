#!/bin/sh
set -eu

DB_WAIT_TIMEOUT="${DB_WAIT_TIMEOUT:-60}"

echo "Waiting up to ${DB_WAIT_TIMEOUT}s for PostgreSQL..."
python <<'PY'
import os
import sys
import time

import django
from django.db import connection

timeout = int(os.environ.get("DB_WAIT_TIMEOUT", "60"))
deadline = time.monotonic() + timeout
last_error = None

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

while time.monotonic() < deadline:
    try:
        connection.ensure_connection()
        connection.close()
        print("PostgreSQL is ready.")
        break
    except Exception as exc:
        last_error = exc
        time.sleep(1)
else:
    print(f"PostgreSQL was not reachable within {timeout}s: {last_error}", file=sys.stderr)
    sys.exit(1)
PY

python manage.py check --deploy
python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec "$@"
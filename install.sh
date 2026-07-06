#!/usr/bin/env bash
set -Eeuo pipefail

APP_NAME="inspection"
SERVICE_NAME="${APP_NAME}.service"
NGINX_SITE_NAME="${APP_NAME}"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${PROJECT_DIR}/.venv"
ENV_FILE="${PROJECT_DIR}/.env"
ENV_EXAMPLE="${PROJECT_DIR}/.env.example"
RUN_DIR="${PROJECT_DIR}/run"
SOCKET_PATH="${RUN_DIR}/gunicorn.sock"
STATIC_ROOT="${PROJECT_DIR}/staticfiles"
MEDIA_ROOT="${PROJECT_DIR}/media"
DJANGO_SETTINGS_MODULE="config.settings"
WSGI_MODULE="config.wsgi:application"
INSTALL_USER="${SUDO_USER:-$(id -un)}"

if [[ "${EUID}" -eq 0 ]]; then
  SUDO=""
else
  SUDO="sudo"
fi

fail() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || fail "Required command not found: $1"
}

read_env_value() {
  local key="$1"
  local line value
  line="$(grep -E "^[[:space:]]*${key}[[:space:]]*=" "${ENV_FILE}" | tail -n 1 || true)"
  [[ -n "${line}" ]] || return 0
  value="${line#*=}"
  value="${value%%#*}"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  value="${value%\"}"
  value="${value#\"}"
  value="${value%\'}"
  value="${value#\'}"
  printf '%s' "${value}"
}

require_env_value() {
  local key="$1"
  local value
  value="$(read_env_value "${key}")"
  [[ -n "${value}" ]] || fail "${key} must be set in ${ENV_FILE}"
}

install_system_dependencies() {
  ${SUDO} apt-get update
  ${SUDO} DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3 \
    python3-venv \
    python3-pip \
    nginx \
    git
}

ensure_env_file() {
  if [[ ! -f "${ENV_FILE}" ]]; then
    [[ -f "${ENV_EXAMPLE}" ]] || fail ".env is missing and .env.example was not found"
    cp "${ENV_EXAMPLE}" "${ENV_FILE}"
    chmod 600 "${ENV_FILE}"
    fail ".env was created from .env.example. Edit ${ENV_FILE} for production, then run ./install.sh again"
  fi
  chmod 600 "${ENV_FILE}"
}

validate_env_file() {
  local django_env debug allowed_hosts secret_key db_port
  django_env="$(read_env_value DJANGO_ENV)"
  debug="$(read_env_value DEBUG)"
  allowed_hosts="$(read_env_value ALLOWED_HOSTS)"
  secret_key="$(read_env_value DJANGO_SECRET_KEY)"
  db_port="$(read_env_value DB_PORT)"

  [[ "${django_env}" == "production" ]] || fail "DJANGO_ENV must be production"
  [[ "${debug,,}" == "false" || "${debug}" == "0" || "${debug,,}" == "no" || "${debug,,}" == "off" ]] || fail "DEBUG must be false"
  [[ -n "${allowed_hosts}" ]] || fail "ALLOWED_HOSTS must be set"
  [[ "${allowed_hosts}" != "127.0.0.1,localhost" ]] || fail "ALLOWED_HOSTS must include production host names"
  [[ -n "${secret_key}" ]] || fail "DJANGO_SECRET_KEY must be set"
  [[ "${secret_key}" != "django-insecure-local-development-only-change-me" ]] || fail "DJANGO_SECRET_KEY must be changed from the development placeholder"
  [[ "${secret_key}" != django-insecure-* ]] || fail "DJANGO_SECRET_KEY must not use a django-insecure placeholder"

  require_env_value DB_NAME
  require_env_value DB_USER
  require_env_value DB_PASSWORD
  require_env_value DB_HOST
  [[ -n "${db_port}" ]] || fail "DB_PORT must be set"
}

setup_python_environment() {
  python3 -m venv "${VENV_DIR}"
  "${VENV_DIR}/bin/python" -m pip install --upgrade pip
  "${VENV_DIR}/bin/pip" install -r "${PROJECT_DIR}/requirements.txt"
}

run_django_setup() {
  mkdir -p "${STATIC_ROOT}" "${MEDIA_ROOT}" "${RUN_DIR}"
  export DJANGO_SETTINGS_MODULE
  "${VENV_DIR}/bin/python" "${PROJECT_DIR}/manage.py" migrate --noinput
  "${VENV_DIR}/bin/python" "${PROJECT_DIR}/manage.py" collectstatic --noinput
}

write_systemd_service() {
  ${SUDO} tee "/etc/systemd/system/${SERVICE_NAME}" >/dev/null <<EOF
[Unit]
Description=Inspection Django Gunicorn Service
After=network.target

[Service]
Type=simple
User=${INSTALL_USER}
Group=www-data
WorkingDirectory=${PROJECT_DIR}
EnvironmentFile=${ENV_FILE}
Environment=DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE}
RuntimeDirectory=${APP_NAME}
Restart=always
RestartSec=5
UMask=0007
ExecStart=${VENV_DIR}/bin/gunicorn ${WSGI_MODULE} --workers 3 --bind unix:${SOCKET_PATH} --access-logfile - --error-logfile -

[Install]
WantedBy=multi-user.target
EOF
}

write_nginx_site() {
  ${SUDO} tee "/etc/nginx/sites-available/${NGINX_SITE_NAME}" >/dev/null <<EOF
server {
    listen 80;
    server_name _;

    client_max_body_size 25m;

    location /static/ {
        alias ${STATIC_ROOT}/;
        access_log off;
        expires 30d;
        add_header Cache-Control "public";
    }

    location /media/ {
        alias ${MEDIA_ROOT}/;
        access_log off;
        expires 7d;
        add_header Cache-Control "public";
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:${SOCKET_PATH};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
    }
}
EOF

  ${SUDO} ln -sfn "/etc/nginx/sites-available/${NGINX_SITE_NAME}" "/etc/nginx/sites-enabled/${NGINX_SITE_NAME}"
  if [[ -L /etc/nginx/sites-enabled/default || -f /etc/nginx/sites-enabled/default ]]; then
    ${SUDO} rm -f /etc/nginx/sites-enabled/default
  fi
  ${SUDO} nginx -t
}

set_permissions() {
  mkdir -p "${RUN_DIR}" "${STATIC_ROOT}" "${MEDIA_ROOT}"
  ${SUDO} chown -R "${INSTALL_USER}:www-data" "${PROJECT_DIR}"
  ${SUDO} find "${PROJECT_DIR}" -type d -exec chmod 750 {} \;
  ${SUDO} find "${PROJECT_DIR}" -type f -exec chmod 640 {} \;
  chmod 750 "${PROJECT_DIR}/manage.py" "${PROJECT_DIR}/install.sh"
  ${SUDO} find "${VENV_DIR}/bin" -maxdepth 1 -type f -exec chmod 750 {} \;
  chmod 600 "${ENV_FILE}"
}

restart_services() {
  ${SUDO} systemctl daemon-reload
  ${SUDO} systemctl enable "${SERVICE_NAME}"
  ${SUDO} systemctl restart "${SERVICE_NAME}"
  ${SUDO} systemctl restart nginx
}

main() {
  require_command grep
  install_system_dependencies
  ensure_env_file
  validate_env_file
  setup_python_environment
  run_django_setup
  set_permissions
  write_systemd_service
  write_nginx_site
  restart_services
  ${SUDO} systemctl --no-pager --full status "${SERVICE_NAME}"
}

main "$@"

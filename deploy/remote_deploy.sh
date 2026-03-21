#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-/srv/convert-api/app}"
SHARED_DIR="${SHARED_DIR:-$(dirname "$APP_DIR")/shared}"
APP_ENV_FILE="${APP_ENV_FILE:-$SHARED_DIR/convert-api.env}"
APP_LOGS_DIR="${APP_LOGS_DIR:-$SHARED_DIR/logs}"
APP_GENERATED_DIR="${APP_GENERATED_DIR:-$SHARED_DIR/generated}"
APP_DOWNLOAD_DIR="${APP_DOWNLOAD_DIR:-$SHARED_DIR/downloaded}"
APP_UID="${APP_UID:-10001}"
APP_GID="${APP_GID:-10001}"
DOCKER_BIN="${DOCKER_BIN:-docker}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"

if [[ ! -d "$APP_DIR" ]]; then
  echo "APP_DIR does not exist: $APP_DIR" >&2
  exit 1
fi

cd "$APP_DIR"
mkdir -p "$SHARED_DIR" "$APP_LOGS_DIR" "$APP_GENERATED_DIR" "$APP_DOWNLOAD_DIR"
chown -R "$APP_UID:$APP_GID" "$APP_LOGS_DIR" "$APP_GENERATED_DIR" "$APP_DOWNLOAD_DIR"

if [[ ! -f "$APP_ENV_FILE" ]]; then
  cp deploy/env/convert-api.env.example "$APP_ENV_FILE"
  echo "Created default env file at $APP_ENV_FILE" >&2
fi

remove_env_key() {
  local key="$1"
  sed -i "/^${key}=/d" "$APP_ENV_FILE"
}

ensure_env_default() {
  local key="$1"
  local value="$2"
  if ! grep -q "^${key}=" "$APP_ENV_FILE"; then
    printf '%s=%s\n' "$key" "$value" >> "$APP_ENV_FILE"
  fi
}

remove_env_key "FEED_SOURCE_PATH"
remove_env_key "FEED_SUPPLEMENTAL_SOURCE_PATH"
ensure_env_default "FEED_SOURCE_URL" "https://fk-inhome.com.ua/productcatalog/rozetka/?uid=8ecf4c810347463c9439b3af4e7cd6e6&lang=3"
ensure_env_default "FEED_SUPPLEMENTAL_SOURCE_URL" "https://fk-inhome.com.ua/productcatalog/prom/?uid=254bde5b79b34ce7ac5f66ad2f63d32c&lang=3"
ensure_env_default "FEED_DOWNLOAD_TIMEOUT" "60"

python3 -m py_compile logger.py main.py api/*.py feed_module/*.py

export APP_ENV_FILE
export APP_LOGS_DIR
export APP_GENERATED_DIR
export APP_DOWNLOAD_DIR

"$DOCKER_BIN" compose -f "$COMPOSE_FILE" up -d --build --remove-orphans
"$DOCKER_BIN" compose -f "$COMPOSE_FILE" ps

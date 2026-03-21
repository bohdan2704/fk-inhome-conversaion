#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-/srv/convert-api/app}"
SHARED_DIR="${SHARED_DIR:-$(dirname "$APP_DIR")/shared}"
APP_ENV_FILE="${APP_ENV_FILE:-$SHARED_DIR/convert-api.env}"
APP_LOGS_DIR="${APP_LOGS_DIR:-$SHARED_DIR/logs}"
APP_GENERATED_DIR="${APP_GENERATED_DIR:-$SHARED_DIR/generated}"
APP_UID="${APP_UID:-10001}"
APP_GID="${APP_GID:-10001}"
DOCKER_BIN="${DOCKER_BIN:-docker}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"

if [[ ! -d "$APP_DIR" ]]; then
  echo "APP_DIR does not exist: $APP_DIR" >&2
  exit 1
fi

cd "$APP_DIR"
mkdir -p "$SHARED_DIR" "$APP_LOGS_DIR" "$APP_GENERATED_DIR"
chown -R "$APP_UID:$APP_GID" "$APP_LOGS_DIR" "$APP_GENERATED_DIR"

if [[ ! -f "$APP_ENV_FILE" ]]; then
  cp deploy/env/convert-api.env.example "$APP_ENV_FILE"
  echo "Created default env file at $APP_ENV_FILE" >&2
fi

python3 -m py_compile logger.py main.py api/*.py feed_module/*.py

export APP_ENV_FILE
export APP_LOGS_DIR
export APP_GENERATED_DIR

"$DOCKER_BIN" compose -f "$COMPOSE_FILE" up -d --build --remove-orphans
"$DOCKER_BIN" compose -f "$COMPOSE_FILE" ps

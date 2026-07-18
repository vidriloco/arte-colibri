#!/usr/bin/env bash
#
# Dev helper for the arte-colibri stack (base + dev override).
# Project name "arte-colibri" (set in docker-compose.yaml) namespaces all
# resources so they don't clash with other apps on this host.
#
# Usage: ./scripts/dev.sh [command] [args...]
#   up        (default) build + start in the foreground with live reload
#   down      stop and remove containers (keeps the DB volume)
#   logs      follow logs
#   ps        list containers
#   restart   restart services
#   build     rebuild images
#   shell     open a bash shell in the app container
#   manage    run ./manage.py inside the app container, e.g.:
#               ./scripts/dev.sh manage migrate
#               ./scripts/dev.sh manage createsuperuser
#   <other>   passed straight through to `docker compose`
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

dc() { docker compose -f docker-compose.yaml -f docker-compose.override.yml "$@"; }

cmd="${1:-up}"
[ $# -gt 0 ] && shift || true

case "$cmd" in
  up)      dc up --build "$@" ;;
  down)    dc down "$@" ;;
  logs)    dc logs -f "$@" ;;
  ps)      dc ps "$@" ;;
  restart) dc restart "$@" ;;
  build)   dc build "$@" ;;
  shell)   dc exec app bash ;;
  manage)  dc exec app python geodjango/manage.py "$@" ;;
  *)       dc "$cmd" "$@" ;;
esac

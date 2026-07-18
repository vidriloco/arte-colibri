#!/usr/bin/env bash
#
# Production deploy helper for the arte-colibri stack (base + prod override).
# Project name "arte-colibri" (set in docker-compose.yaml) namespaces all
# resources so they don't clash with other apps on this host.
#
# Usage: ./scripts/prod.sh [command] [args...]
#   up        (default) build + start detached, then show status
#   down      stop and remove containers (keeps the DB volume)
#   logs      follow logs
#   ps        list containers
#   migrate   apply DB migrations
#   manage    run ./manage.py inside the app container
#   shell     open a bash shell in the app container
#   <other>   passed straight through to `docker compose`
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

dc() { docker compose -f docker-compose.yaml -f docker-compose.prod.yml "$@"; }

cmd="${1:-up}"
[ $# -gt 0 ] && shift || true

case "$cmd" in
  up)
    dc up -d --build "$@"
    echo
    dc ps
    echo
    echo "Deployed. Apply migrations next:  ./scripts/prod.sh migrate"
    ;;
  down)    dc down "$@" ;;
  logs)    dc logs -f "$@" ;;
  ps)      dc ps "$@" ;;
  migrate) dc exec app python geodjango/manage.py migrate "$@" ;;
  manage)  dc exec app python geodjango/manage.py "$@" ;;
  shell)   dc exec app bash ;;
  *)       dc "$cmd" "$@" ;;
esac

#!/usr/bin/env bash
#
# Production deploy helper for the arte-colibri stack (base + prod override).
# Project name "arte-colibri" (set in docker-compose.yaml) namespaces all
# resources so they don't clash with other apps on this host.
#
# Usage: ./scripts/prod.sh [command] [args...]
#   up        (default) one-shot deploy: pull latest main, prepare .env,
#             build + start, apply migrations, install/refresh the Apache
#             vhost, show status
#   apache    (re)install the Apache vhost for APP_DOMAIN and reload Apache
#   down      stop and remove containers (keeps the DB volume)
#   logs      follow logs
#   ps        list containers
#   migrate   apply DB migrations
#   manage    run ./manage.py inside the app container
#   shell     open a bash shell in the app container
#   <other>   passed straight through to `docker compose`
#
# `up` maintains a git-ignored .env next to the compose files:
#   APP_DOMAIN              your public domain (e.g. artecolibri.mx) — drives
#                           the Apache vhost, ALLOWED_HOSTS and CSRF origins
#   DJANGO_SECRET_KEY       generated on first run, then left untouched
#   DJANGO_DEBUG            forced to False
#   DJANGO_ALLOWED_HOSTS /  derived from APP_DOMAIN when empty; edit freely,
#   CSRF_TRUSTED_ORIGINS    your values are preserved on later runs
#   TURNSTILE_SITE_KEY /    Cloudflare Turnstile credentials — scaffolded empty;
#   TURNSTILE_SECRET_KEY    paste yours from the Cloudflare dashboard
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

dc() { docker compose -f docker-compose.yaml -f docker-compose.prod.yml "$@"; }

ENV_FILE="$ROOT/.env"
SUDO=""
[ "$(id -u)" -ne 0 ] && SUDO="sudo"

# Read the value of $1 from .env (empty output if the key is absent).
env_get() { sed -n "s/^$1=//p" "$ENV_FILE" 2>/dev/null | tail -n 1; }

# Set KEY=value, replacing an existing line or appending a new one.
env_set() {
  if grep -q "^$1=" "$ENV_FILE" 2>/dev/null; then
    sed -i.bak "s|^$1=.*|$1=$2|" "$ENV_FILE" && rm -f "$ENV_FILE.bak"
  else
    printf '%s=%s\n' "$1" "$2" >> "$ENV_FILE"
  fi
}

# Append "KEY=value" only if KEY is missing from .env entirely.
env_ensure_line() {
  grep -q "^$1=" "$ENV_FILE" 2>/dev/null || printf '%s=%s\n' "$1" "$2" >> "$ENV_FILE"
}

ensure_env() {
  [ -f "$ENV_FILE" ] || { umask 077; : > "$ENV_FILE"; }

  # Public domain: everything host-related derives from this one value.
  env_ensure_line APP_DOMAIN ""
  local domain
  domain="$(env_get APP_DOMAIN)"
  if [ -n "$domain" ]; then
    [ -n "$(env_get DJANGO_ALLOWED_HOSTS)" ] \
      || env_set DJANGO_ALLOWED_HOSTS "$domain,www.$domain,127.0.0.1,localhost"
    [ -n "$(env_get CSRF_TRUSTED_ORIGINS)" ] \
      || env_set CSRF_TRUSTED_ORIGINS "https://$domain,https://www.$domain"
  else
    echo "NOTE: APP_DOMAIN is empty in .env — set it (e.g. APP_DOMAIN=artecolibri.mx)" >&2
    echo "      and rerun to derive ALLOWED_HOSTS/CSRF origins and set up Apache." >&2
  fi

  # Secret key: generate once, never rotate silently (rotating invalidates sessions).
  if [ -z "$(env_get DJANGO_SECRET_KEY)" ]; then
    env_set DJANGO_SECRET_KEY "$(openssl rand -hex 50)"
    echo "Generated DJANGO_SECRET_KEY in .env"
  fi

  # Debug must be off in production, whatever .env says.
  env_set DJANGO_DEBUG False

  # Cloudflare Turnstile — scaffold the keys so they're loaded once filled in.
  env_ensure_line TURNSTILE_SITE_KEY ""
  env_ensure_line TURNSTILE_SECRET_KEY ""
  if [ -z "$(env_get TURNSTILE_SITE_KEY)" ] || [ -z "$(env_get TURNSTILE_SECRET_KEY)" ]; then
    echo "WARNING: TURNSTILE_SITE_KEY / TURNSTILE_SECRET_KEY are empty in .env —" >&2
    echo "         paste your Cloudflare Turnstile keys there and rerun to enable it." >&2
  fi
}

pull_latest() {
  # Deploy from the tip of main. Quietly steps aside when there's nothing to
  # pull from (no git, no origin — e.g. a copied directory), warns when the
  # checkout isn't main, and refuses to guess when histories diverged.
  command -v git >/dev/null 2>&1 || return 0
  git -C "$ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1 || return 0
  if ! git -C "$ROOT" remote get-url origin >/dev/null 2>&1; then
    echo "No 'origin' remote — skipping git pull."
    return 0
  fi
  local branch
  branch="$(git -C "$ROOT" rev-parse --abbrev-ref HEAD)"
  if [ "$branch" != "main" ]; then
    echo "WARNING: checked out on '$branch', not main — skipping git pull." >&2
    return 0
  fi
  echo "Pulling latest main..."
  git -C "$ROOT" fetch origin main
  if ! git -C "$ROOT" merge --ff-only origin/main; then
    echo "ERROR: local main has diverged from origin/main — resolve manually," >&2
    echo "       then rerun ./scripts/prod.sh up" >&2
    return 1
  fi
}

migrate_db() {
  echo "Applying database migrations..."
  local i
  for i in 1 2 3 4 5 6 7 8 9 10; do
    if dc exec -T app python geodjango/manage.py migrate --noinput; then
      return 0
    fi
    echo "App not ready yet (attempt $i/10), retrying in 3s..."
    sleep 3
  done
  echo "ERROR: could not apply migrations — check './scripts/prod.sh logs app'." >&2
  return 1
}

configure_apache() {
  # Debian/Ubuntu Apache layout (a2enmod & friends). Elsewhere (e.g. a dev Mac
  # or a distro without apache2) this quietly steps aside.
  if ! command -v a2enmod >/dev/null 2>&1; then
    echo "Apache (a2enmod) not found on this host — skipping vhost setup."
    return 0
  fi
  local domain
  domain="$(env_get APP_DOMAIN)"
  if [ -z "$domain" ]; then
    echo "APP_DOMAIN empty in .env — skipping Apache vhost setup." >&2
    return 0
  fi

  local vhost=/etc/apache2/sites-available/arte-colibri.conf
  local tmp
  tmp="$(mktemp)"
  # The repo template uses artecolibri.mx as the placeholder domain.
  sed "s/artecolibri\.mx/$domain/g" "$ROOT/deploy/apache/arte-colibri.conf" > "$tmp"

  $SUDO a2enmod -q proxy proxy_http headers ssl rewrite
  if ! cmp -s "$tmp" "$vhost" 2>/dev/null; then
    $SUDO cp "$tmp" "$vhost"
    echo "Installed Apache vhost for $domain"
  fi
  rm -f "$tmp"
  $SUDO a2ensite -q arte-colibri
  $SUDO apachectl configtest
  $SUDO systemctl reload apache2
  echo "Apache configured for $domain (proxy -> 127.0.0.1:8100)."

  if [ ! -e "/etc/letsencrypt/live/$domain" ]; then
    echo
    echo "TLS certificate not found yet. Issue one with:"
    echo "  sudo certbot --apache -d $domain -d www.$domain"
  fi
}

cmd="${1:-up}"
[ $# -gt 0 ] && shift || true

case "$cmd" in
  up)
    pull_latest
    ensure_env
    dc up -d --build "$@"
    migrate_db
    configure_apache
    echo
    dc ps
    echo
    echo "Deploy complete."
    ;;
  apache)  ensure_env; configure_apache ;;
  down)    dc down "$@" ;;
  logs)    dc logs -f "$@" ;;
  ps)      dc ps "$@" ;;
  migrate) dc exec app python geodjango/manage.py migrate "$@" ;;
  manage)  dc exec app python geodjango/manage.py "$@" ;;
  shell)   dc exec app bash ;;
  *)       dc "$cmd" "$@" ;;
esac

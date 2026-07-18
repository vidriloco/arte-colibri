# Arte Colibrí

A curated digital gallery for local artists in Mexico City. Visitors discover and
**inquire** about artwork (no cart, no checkout); artists upload and submit work;
curators review, approve, and feature it. Spanish-first, bilingual (ES/EN).

## Architecture

- **Backend** — Django + GeoDjango (PostGIS) exposing a JSON API via Django REST
  Framework under `/api/`. Project root `geodjango/`, single app `world`
  (models in `world/models/`, API in `world/api/`).
- **Frontend** — a ReactJS single-page app (Vite) in `frontend/`, consuming the
  `/api/` contract. Bilingual UI; bespoke design system ported as plain CSS
  (`frontend/src/styles.css`).
- **Media** — user-uploaded images under `/media/` (a named Docker volume).
- Curation is editorial: artwork moves through `draft → submitted → published`
  (or `rejected`); **only published content is publicly reachable** (enforced at the
  queryset layer). Curators can **feature** pieces. Commerce is display-price +
  inquire only — no payments.

See `openspec/changes/` for the specs: `artist-showcase-mvp` (domain),
`json-content-api` (the API), `react-spa-frontend` (the SPA), and
`manage-page-seo` (dashboard-managed, server-injected SEO).

## Run it (Docker, dev)

```bash
docker compose up -d --build          # Postgres/PostGIS + Django (app) + Vite (frontend)
# one-time DB setup, run inside the app container:
docker compose exec app python geodjango/manage.py migrate
docker compose exec app python geodjango/manage.py seed_demo
```

- API:      http://localhost:8100/api/
- SPA:      http://localhost:5173/  (Vite dev server; proxies `/api` + `/media` to the app)
- Admin:    http://localhost:8100/admin/

Prefer running the SPA on the host instead of the `frontend` container?

```bash
cd frontend
npm install
npm run dev            # http://localhost:5173  (proxies to http://localhost:8100)
npm run build          # production bundle in frontend/dist
```

## Demo accounts (created by `seed_demo`)

- **Curator** — `curador@artecolibri.mx` / `colibri123`
- **Artist**  — `mariana-quiroz@artecolibri.mx` / `colibri123` (and one login per seeded artist)

Sign in from the SPA's **Acceder** / dashboard route. New artists self-register
through the **Aplicar** flow (account → profile + first artwork → submit for review).

## API surface (under `/api/`)

| Area        | Endpoints |
|-------------|-----------|
| Public      | `home/`, `artworks/` (`?tag=&sort=&page=`), `artworks/<slug>/`, `artists/`, `artists/<slug>/`, `locations/`, `meta/`, `seo/?page=<key>` |
| Inquiry     | `POST artworks/<slug>/inquiries/` |
| Auth        | `auth/signup/`, `auth/login/`, `auth/logout/`, `auth/me/` |
| Dashboard   | `dashboard/profile/`, `dashboard/artworks/…` (CRUD, `submit/`, `images/…`), `dashboard/inquiries/` |
| Curation    | `curation/queue/`, `curation/artworks/<id>/{approve,reject,feature}/`, `curation/artists/<id>/{approve,reject}/`, `curation/inquiries/`, `curation/seo/` (+ `<key>/`, `<key>/image/`) |

Bilingual fields (artwork title/medium/description, artist bio/discipline, tag/region
labels) are returned as `{ "es": …, "en": … }`; the SPA switches language client-side.

## SEO (dashboard-managed, server-injected)

Curators edit the SEO of the main pages — **Home, Gallery, Artists, Browse-by-location**,
plus a site-wide **default** slot — from the **SEO** tab in the curator dashboard: bilingual
meta title/description, Open Graph title/description, an OG image, canonical, and a robots
directive. Values resolve per-field (page → `default` → built-in default).

Delivery is **server-side** so crawlers and link-preview scrapers see the right tags on the
first response: for every public route Django serves the built SPA's `index.html` with the
resolved `<head>` injected (`world/seo.py` → `AppShellView`, wired as the catch-all in
`geodjango/urls.py`). Detail routes (`/artwork/:slug`, `/artist/:slug`) aren't dashboard
slots — their meta is derived from the published item (title, description, primary image).
The SPA also keeps the head in sync during client-side navigation and language toggling
(`frontend/src/head.js`). Spanish is the server-rendered default language.

## Run it (Docker, prod)

Server-injected SEO requires Django to serve the **built** SPA:

```bash
npm --prefix frontend run build         # Vite builds with base=/static/ → frontend/dist
docker compose -f docker-compose.yaml -f docker-compose.prod.yml up -d --build
docker compose exec app python geodjango/manage.py collectstatic --noinput
```

Set via env (see `docker-compose.prod.yml`): `DJANGO_DEBUG=False`,
`DJANGO_ALLOWED_HOSTS`, `DJANGO_SECRET_KEY`. WhiteNoise serves the hashed assets under
`/static/`; Django serves the SEO-injected shell for every other route.

## Tests

```bash
docker compose exec app python geodjango/manage.py test world
```

Covers visibility gating (published-only / 404), curation transitions
(approve / reject-requires-notes / feature-requires-published / role enforcement),
ownership (no cross-edit, no self-publish), inquiries, image upload, and the
bilingual contract.

## Notes / follow-ups

- **SEO** — page `<head>` (title/description/OG/canonical/robots) is now dashboard-managed
  and **server-injected** for all public routes (see above). What is *not* server-rendered is
  the page **body**: the DOM is still hydrated client-side, so full-content SSR/prerender (for
  crawlers that don't execute JS and need body text) remains a follow-up.
- **WSGI server** — prod still uses `runserver` unless `gunicorn` is added to
  `requirements.txt` and enabled in `docker-compose.prod.yml`.
- **Media in prod** — dev uses a named volume; object storage (`django-storages`/S3)
  is a likely follow-up.
- **Auth** — DRF token + session today; JWT is a possible later swap behind the same
  endpoints.

---

## Original infra notes

### How to migrate down

`python3 manage.py migrate world 0001` will undo migrations after 0001.

### Show the available migrations

`python3 manage.py showmigrations world`

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
| Dashboard   | `dashboard/profile/` (+ `avatar/`), `dashboard/artworks/…` (CRUD, `submit/`, `images/…`), `dashboard/inquiries/` |
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

## Image storage (AWS S3)

Artist-uploaded images — artwork images with their generated thumbnails, and artist
profile avatars — are stored in the **`arte-colibri` S3 bucket**, not on the local disk.
The upload code (`world/utils/s3.py`) is a direct-`boto3` service: it builds a client from
settings, writes public-read objects under deterministic keys, and persists the object's
**public URL** on the model (`ArtworkImage.external_url` / `.thumbnail_url`,
`Artist.avatar_url`). Object keys:

```
artists/avatars/<artist-slug>-<artist-id>.<ext>
artworks/<artwork-slug>/<image-id>.<ext>
artworks/<artwork-slug>/thumbs/<image-id>.jpg
```

**Upload endpoints** (owner-authenticated; rejected 401/403 otherwise):

- `POST dashboard/artworks/<id>/images/` — add an artwork image, **≤ 500 KB**.
- `DELETE dashboard/artworks/<id>/images/<image_id>/` — removes the S3 objects too.
- `POST dashboard/profile/avatar/` — upload/replace the avatar, **≤ 200 KB**.

The size limit and image validation run **before** anything is written to S3
(`world/imaging.py`: `validate_image(file, max_bytes=…)`); oversized or non-image uploads
get a `400`. When AWS credentials are missing the upload fails loudly rather than falling
back to local disk.

**Configuration** — set in the git-ignored `.env` (dev) / prod `.env`:

```
AWS_ACCESS_KEY_ID=…        # IAM key with s3:PutObject / s3:DeleteObject on the bucket
AWS_SECRET_ACCESS_KEY=…
AWS_S3_REGION=us-east-2
AWS_S3_BUCKET_NAME=arte-colibri
```

The bucket must serve its objects publicly (public-read) so image URLs load in the browser.
Because `boto3` was added to `requirements.txt`, rebuild the image (`./scripts/dev.sh build`
/ `./scripts/prod.sh up`) so it is installed.

## API keys & AI SEO generation

Curators can store third-party API keys from the dashboard's **API keys** tab
(`curation/api-keys/`). Each key is a **type + secret value**; the secret is **write-only** —
the API only ever returns a masked `…last4` preview, never the raw value, and only curators can
read or write. Keys live in the DB (plaintext at rest — encryption is a follow-up) so they can
be rotated without a redeploy.

With an **OpenRouter** key configured, each slot in the **SEO** tab shows a **Generate** button.
It reads that slot's description (Spanish preferred, English otherwise), calls OpenRouter
server-side, and fills every SEO field — meta title/description, social title/description,
keywords, image alt — **in both ES and EN**. The result is a *draft*: the curator reviews and
clicks Save; nothing persists automatically, and the key never reaches the browser.

The model is chosen per key from three price/power-equivalent options —
`anthropic/claude-3.5-haiku`, `openai/gpt-4o-mini`, `google/gemini-2.0-flash-001`. Optional env:
`OPENROUTER_MODEL` (override the default when a key has none set) and `OPENROUTER_BASE_URL`.
Generation fails clearly when no key is set (409), the description is empty (400), or the
provider errors (502), and never partially saves.

## Run it (Docker, prod)

One command deploys everything:

```bash
./scripts/prod.sh up
```

That single shot: pulls the latest `main` from origin (fast-forward only; skipped
when there's no remote), maintains a git-ignored `.env` (generates `DJANGO_SECRET_KEY`
on first run, forces `DJANGO_DEBUG=False`, derives `DJANGO_ALLOWED_HOSTS` and
`CSRF_TRUSTED_ORIGINS` from `APP_DOMAIN`, scaffolds the Cloudflare Turnstile
keys), builds the image (a Node stage compiles the SPA with `base=/static/` and
`collectstatic` runs at build time, so assets are always fresh), starts the
stack, applies migrations, and — on a Debian/Ubuntu host with Apache — installs
the vhost from `deploy/apache/` for `APP_DOMAIN` and reloads Apache.

First deploy on a new server:

```bash
./scripts/prod.sh up                      # scaffolds .env, then:
$EDITOR .env                              # set APP_DOMAIN + Turnstile keys
./scripts/prod.sh up                      # full one-shot deploy
./scripts/prod.sh manage createsuperuser  # once
sudo certbot --apache -d <domain> -d www.<domain>   # TLS, once
```

Gunicorn serves the app on `127.0.0.1:8100` (loopback only); Apache terminates
TLS in front. WhiteNoise serves the hashed assets under `/static/`; Django
serves the SEO-injected shell for every other route.

## Tests

```bash
docker compose exec app python geodjango/manage.py test world
```

Covers visibility gating (published-only / 404), curation transitions
(approve / reject-requires-notes / feature-requires-published / role enforcement),
ownership (no cross-edit, no self-publish), inquiries, image/avatar upload to S3
(size limits, ownership, delete-removes-objects; the S3 client is mocked so tests need
no live bucket), and the bilingual contract.

## Notes / follow-ups

- **SEO** — page `<head>` (title/description/OG/canonical/robots) is now dashboard-managed
  and **server-injected** for all public routes (see above). What is *not* server-rendered is
  the page **body**: the DOM is still hydrated client-side, so full-content SSR/prerender (for
  crawlers that don't execute JS and need body text) remains a follow-up.
- **WSGI server** — prod still uses `runserver` unless `gunicorn` is added to
  `requirements.txt` and enabled in `docker-compose.prod.yml`.
- **Media** — new artist uploads go to **AWS S3** (see *Image storage* above). Two
  follow-ups remain: backfilling any pre-S3 images from the local `media` volume into the
  bucket, and dropping the now-deprecated `ImageField`s (`ArtworkImage.image/thumbnail`,
  `Artist.avatar`) once that backfill is done.
- **Auth** — DRF token + session today; JWT is a possible later swap behind the same
  endpoints.

---

## Original infra notes

### How to migrate down

`python3 manage.py migrate world 0001` will undo migrations after 0001.

### Show the available migrations

`python3 manage.py showmigrations world`

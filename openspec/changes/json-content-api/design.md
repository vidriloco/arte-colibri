## Context

`artist-showcase-mvp` defines the domain (Artist, Artwork, ArtworkImage, Inquiry), the curation state machine (`draft → submitted → published`/`rejected`), and the `Artist`/`Curator` role groups, all on Django + PostGIS. The companion `react-spa-frontend` change moves the UI to a ReactJS SPA. A SPA cannot consume Django template context, so the domain must be exposed as a JSON HTTP API. This change designs that API: the single contract every public screen, the artist apply flow, and the management dashboard depend on.

The existing stack is Django 3.1-era settings on Python, PostGIS, run in Docker. There is no API layer today (one `index` view rendering a template).

## Goals / Non-Goals

**Goals:**
- A stable JSON contract under `/api/` covering: public read (published-only), auth + artist signup, owner-scoped dashboard CRUD, curator-only curation actions, and inquiry submission.
- Enforce the editorial gate in the **queryset** (`Artwork.published`), so unpublished content can never leak through the API regardless of client behavior.
- Bilingual field payloads (`{es, en}`) so the SPA toggles language without refetching.
- Multipart image upload that yields ordered `ArtworkImage` rows with a primary + generated thumbnail.
- Reuse Django auth, groups, and permissions; keep ownership checks simple and centralized.

**Non-Goals:**
- The React app itself, its routing, i18n UI, or styling (owned by `react-spa-frontend`).
- The domain models, migrations, curation transitions, and role seeding themselves (owned by `artist-showcase-mvp`; this change consumes them).
- Payments/cart/checkout — inquire-only.
- Public SSR/SEO/prerendering (follow-up in the frontend change).
- A versioned/public third-party API; this is an internal contract for our own SPA.

## Decisions

- **Django REST Framework (DRF).** Mature, integrates with Django auth/permissions/pagination, and matches the team's Django stack. *Alternatives:* hand-rolled JSON views (more boilerplate, error-prone serialization) or Django Ninja (less ecosystem familiarity) — rejected.
- **Read/write split with explicit serializers per audience.** Public serializers expose only published-safe fields; dashboard serializers expose ownership/status fields; curator serializers add review fields. Prevents accidental field leakage. *Alternative:* one serializer with conditional fields — rejected as leak-prone.
- **Published gate via the model manager, not the view.** Every public viewset's `get_queryset()` starts from `Artwork.published` / published artists. Tests assert that a `submitted`/`draft`/`rejected` id returns 404 on public routes. *Alternative:* filter in serializer/template — rejected (the spec risk called out in `artist-showcase-mvp`).
- **Auth: session + token (DRF `TokenAuthentication` + `SessionAuthentication`).** Session supports same-site browser use; token supports the SPA storing a bearer credential. `/api/auth/signup` provisions a `User` + `Artist` profile in the `Artist` group; `/api/auth/login` returns a token; `/api/auth/me` returns the current user + role + linked artist. *Alternative:* JWT (`simplejwt`) — viable but adds refresh-token complexity not needed for MVP; can swap later behind the same endpoints.
- **Artist self-signup overrides the prior "invite-only" open question** from `artist-showcase-mvp`, because the design's apply flow requires it. New artists land with `status=draft` content and an unpublished profile until a curator approves.
- **Bilingual fields as nested objects.** Models store bilingual copy (e.g. `title_es`/`title_en`), serialized as `{"es": ..., "en": ...}`. Single-language/numeric fields (price, year, dimensions, slug) stay flat. The SPA picks the active language locally.
- **Filtering/sorting/pagination conventions.** Gallery list accepts `?tag=` (repeatable, AND-combined), `?sort=recent|price_asc|price_desc`, and page-number pagination (`?page=`, fixed page size). Browse-by-location groups published works by the artist's `region`.
- **Curation actions as explicit POST sub-routes** (`/api/dashboard/artworks/{id}/submit`, `/api/curation/artworks/{id}/approve|reject|feature`) rather than PATCHing `status` directly — keeps the state machine authoritative and lets reject require `notes`.
- **CORS via `django-cors-headers`**, allowing the SPA dev origin (Vite) and configured production origin. Media (`MEDIA_URL`) served by Django in dev so image URLs resolve cross-origin.

## Risks / Trade-offs

- **Unpublished content leaking through any endpoint** → centralize on `Artwork.published`/published-artist querysets; add visibility-gating tests for every public route (404 on non-published ids).
- **Over-exposing fields per role** → separate serializers per audience + tests asserting dashboard/curator-only fields never appear in public responses.
- **CORS/auth misconfiguration between origins** → pin `CORS_ALLOWED_ORIGINS`; prefer token auth for the SPA to avoid CSRF/cookie cross-site friction; document the dev origins.
- **Image upload abuse (size/type)** → validate content type and max dimensions/size with Pillow before persisting; generate thumbnails to bound payload size.
- **SEO regression from SPA** → out of scope here; flagged for the frontend change (prerender/SSR follow-up).
- **API/SPA contract drift** → both changes ship together; the bilingual nested-object shape and endpoint list in `specs/http-api/spec.md` are the single source of truth.

## Migration Plan

- Additive: add DRF + cors-headers to `requirements.txt`; add `rest_framework`, `rest_framework.authtoken`, `corsheaders` to `INSTALLED_APPS`; add `REST_FRAMEWORK`, `CORS_ALLOWED_ORIGINS`, `MEDIA_URL/MEDIA_ROOT` to settings; add corsheaders middleware.
- Mount the API at `/api/` in `geodjango/urls.py` alongside the existing routes; serve media in dev (`DEBUG`).
- Token table migration (`authtoken`).
- Depends on `artist-showcase-mvp` migrations being applied first (models, groups).
- Rollback: unmount `/api/`, remove the apps from settings; no destructive data changes.

## Open Questions

- **Token vs JWT** long-term — start with DRF token; revisit if mobile/refresh needs appear.
- **Rate limiting** on inquiry submission (anti-spam) — DRF throttling is a likely fast-follow; not blocking for MVP.
- **Inquiry email notifications** — API records inquiries; email delivery deferred (same stance as `artist-showcase-mvp`).

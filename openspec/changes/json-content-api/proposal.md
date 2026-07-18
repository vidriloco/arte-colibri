## Why

Arte Colibrí is pivoting its frontend to a ReactJS single-page app (see the companion `react-spa-frontend` change), which replaces the prior "server-rendered Django templates" decision. A SPA needs a JSON contract to talk to: the domain defined in `artist-showcase-mvp` (artists, artworks, images, inquiries, curation workflow) must be reachable over HTTP as JSON instead of being baked into Django templates. This change establishes that API layer — the boundary every screen and dashboard action goes through.

## What Changes

- Introduce a **JSON HTTP API** (Django REST Framework) under `/api/` that exposes the `artist-showcase-mvp` domain.
- **Public, read-only endpoints** return *only published* content (the editorial gate is enforced in the queryset, never the client): home feed (featured-then-recent), gallery list (tag filter, sort, pagination), artwork detail (with ordered images), artist profile + their published works, and works grouped by region for browse-by-location. Requesting unpublished/non-existent content returns 404.
- **Authentication & artist signup**: session + token auth, login/logout, current-user (`/api/auth/me`), and self-service artist signup that provisions an `auth.User` in the `Artist` group with a linked `Artist` profile (overrides the earlier "invite-only" assumption to support the design's apply flow).
- **Authenticated dashboard endpoints** (owner-scoped): artist profile read/update, artwork CRUD, multi-image upload + reorder + set-primary, submit-for-review, and an inquiries inbox scoped to the artist's own works.
- **Curation endpoints** (curator/admin only): review queue of submitted artworks/profiles, approve / reject-with-notes / feature actions, and an all-inquiries inbox.
- **Inquiry submission**: an unauthenticated visitor can POST an inquiry against a published artwork (name, email, message) with server-side validation.
- **Bilingual payloads**: text fields that are bilingual in the design (artwork title, medium, description; artist bio/statement; tag/region labels) are returned with both `es` and `en` values so the SPA can switch language client-side without refetching.
- All responses are **inquire-only** — no cart, checkout, order, or payment endpoints exist.

## Capabilities

### New Capabilities
- `http-api`: the REST/JSON API surface — resource shapes, public read endpoints (published-only), authenticated owner-scoped dashboard endpoints, curator-only curation endpoints, inquiry submission, auth/signup, pagination/filtering/sorting conventions, error/404 semantics, and the bilingual field contract.

### Modified Capabilities
<!-- Baseline specs (openspec/specs/) are empty; artist-showcase-mvp is not yet archived. No baseline requirements to modify here. The frontend-delivery shift is captured in the react-spa-frontend change. -->
- None.

## Impact

- **Backend (`geodjango/world`)**: add Django REST Framework; new `serializers.py`, `api/` views (or DRF viewsets) and `api/urls.py` mounted at `/api/`; DRF permission classes/mixins for owner-only and curator-only access reusing the `Artist`/`Curator` groups from `artist-showcase-mvp`; token auth model/migration; image upload handling (multipart) producing `ArtworkImage` rows + thumbnails.
- **Dependencies**: `djangorestframework`, `django-cors-headers` (the SPA is served from a separate origin in dev), and `Pillow` (already required by `artist-showcase-mvp`) added to `requirements.txt`.
- **Settings**: `REST_FRAMEWORK` config, `CORS_ALLOWED_ORIGINS`, auth backends; `MEDIA_URL`/`MEDIA_ROOT` served in dev so the SPA can render uploaded images.
- **Depends on** `artist-showcase-mvp` for the underlying models, managers (`Artwork.published`), curation state machine, and role groups.
- **SEO note**: a SPA loses server-rendered crawlable HTML; indexability is owned by `react-spa-frontend` (prerender/SSR follow-up), not this API change.

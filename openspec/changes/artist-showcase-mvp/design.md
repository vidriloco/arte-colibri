## Context

The codebase is a GeoDjango project (`geodjango/`, app `world`) with PostGIS, server-rendered Django templates, and Bootstrap. There is currently no domain model — just an `index` view rendering a Bootstrap "cover" placeholder. This design covers the MVP that turns it into a curated showcase: data model, the curation gate, the public pages, and the management dashboard. It qualifies for a design doc because it introduces the full data model, a moderation workflow, role-based access, and user-uploaded media (storage + migration concerns).

## Goals / Non-Goals

**Goals:**
- A coherent data model for artists, artworks, images, and inquiries.
- An editorial gate where *only published content is ever publicly reachable*, enforced at the query layer (not just in templates).
- A visitor home page that communicates "curated artwork from local artists" within the first viewport.
- A dashboard where artists manage their own work and curators approve/feature it — without exposing raw Django admin.
- Reuse the existing server-rendered Django + Bootstrap stack and PostGIS.

**Non-Goals:**
- Online transactions: no cart, checkout, or payments (inquire-to-contact only).
- A SPA / separate frontend framework.
- Location as a headline feature (it is a secondary "browse by location" section).
- Public artist self-service signup flows beyond MVP (account provisioning is curator/admin-driven for now).
- Advanced search, recommendations, or analytics.

## Decisions

- **Server-rendered Django templates + Bootstrap** (not a SPA). Rationale: matches the existing stack and team velocity; SEO is straightforward for indexable showcase content. *Alternative:* React SPA — rejected as unnecessary complexity for a content-display MVP.
- **`Artist` is a profile linked one-to-one to `auth.User`.** Curators/admins are `auth.User`s in a `Curator` group; artists are users in an `Artist` group with an `Artist` profile row. Rationale: leverages Django auth/permissions; keeps per-artist ownership checks simple. *Alternative:* standalone artist records with no login — rejected, since artists need dashboard access.
- **Moderation as an explicit status field** (`draft`, `submitted`, `published`, `rejected`) on `Artwork` (and on `Artist` profiles), with `reviewed_by`, `reviewed_at`, and `review_notes`. Public visibility is enforced through a custom manager (`Artwork.published`) used by every public view, so unpublished work cannot leak. *Alternative:* a separate `Review` table — deferred; a status field is sufficient for MVP and simpler to query.
- **Featured pieces** via a `featured` boolean (+ optional `featured_order`) set only by curators; the home page surfaces featured-then-recent published works.
- **Images:** `ArtworkImage` rows (FK to `Artwork`, `position`, `is_primary`) stored as `ImageField` under `MEDIA_ROOT`, processed with `Pillow` (validation + a generated thumbnail). Supports multiple images with one primary. *Alternative:* single image on `Artwork` — rejected; galleries need multiple.
- **Price & availability:** nullable `price` (`DecimalField`) + `currency` (default configurable, single currency for MVP) + `availability` enum (`available`, `sold`, `not_for_sale`). The detail page shows price when set and always offers **Inquire**.
- **Location:** `city`/`region` text on `Artist` (and optional `PointField` for future mapping). "Browse by location" filters published artworks by their artist's region. Kept as a secondary section per scope.
- **Dashboard at `/dashboard`**, login-required, role-gated views (artists see/edit only their own; curators see all + review actions). Rationale: tailored, safe UX. *Alternative:* customize Django admin — rejected as not artist-friendly and over-exposing.

## Risks / Trade-offs

- **Unpublished content leaking to the public** → enforce a `published` manager/queryset on every public view and cover it with tests; never filter only in templates.
- **Media persistence in production** → store `MEDIA_ROOT` on a named Docker volume now; plan `django-storages` + object storage as a follow-up. Without this, uploads are lost on container replacement (same class of bug as the DB-volume fix already applied).
- **Large/abusive image uploads** → validate type and max dimensions/size with `Pillow`; generate thumbnails to control page weight.
- **Curation bottleneck** (single human queue) → acceptable for MVP; review notes + status make it auditable.
- **Scope size** → tasks are ordered so the data model + public showcase can ship before full dashboard polish; the dashboard can start minimal (forms) and grow.

## Migration Plan

- Additive: new models + migrations; no destructive changes to existing data (there is none).
- Replace the `index` view/template with the new home page; keep the URL `/`.
- Add a data migration (or management command) to create the `Artist` and `Curator` groups with permissions, and seed an initial curator.
- Add `MEDIA_ROOT`/`MEDIA_URL` settings and a media volume to the compose files before enabling uploads in production.
- Rollback: revert templates/views and unapply migrations; uploaded media on the volume is unaffected.

## Open Questions

- **Account provisioning:** invite-only artist accounts (curator-created) vs public artist signup. MVP proposes curator/admin-created accounts; revisit after launch.
- **Internationalization:** the brand ("Arte Colibrí") suggests a Spanish-first or bilingual audience. Defer i18n wiring but write templates so copy is easy to translate later.
- **Currency:** single configurable default (e.g. MXN) for MVP vs multi-currency per artwork. Proposes single default.
- **Inquiry delivery:** in-dashboard inbox only vs also emailing the artist/curator. MVP records in-dashboard; email notification is a likely fast-follow.

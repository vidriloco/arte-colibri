## Why

Arte Colibrí today is a single placeholder landing page (the `world` app with one `index` template) and has no data model. To become a curated community showcase, the site needs to model artists and their artwork, gate what becomes public behind an editorial review, present a visitor experience that immediately reads as *"curated artwork by local artists,"* and give artists and curators a place to manage it all. This change establishes that foundation as an MVP.

## What Changes

- Introduce the core domain — **artist profiles** and an **artwork catalog** (images, medium, dimensions, year, description, price, availability, optional location) — persisted in PostgreSQL/PostGIS.
- Add an **editorial curation workflow**: artworks and artist profiles move through `draft → submitted → published` (or `rejected`); only published content is publicly visible. Curators can **feature** standout pieces.
- Build the **public showcase**: a redesigned home page whose hero and featured grid make the "curated artwork from local artists" identity obvious on arrival; a browsable gallery; artwork detail pages showing price and an **Inquire** action (no online payments); artist profile pages; and a secondary "browse by location" section.
- Build a **management dashboard** (authenticated, distinct from raw Django admin): artists manage their own profile and artworks and submit them for review; curators/admins review the queue, approve/reject/feature, and read inquiries.
- Add an **inquiry** flow: a visitor contacts about a specific piece; the inquiry is recorded and surfaced to the artist/curator in the dashboard.
- **BREAKING (UX):** the current placeholder `index` landing page is replaced by the new showcase home page.

## Capabilities

### New Capabilities
- `artist-profiles`: the Artist entity and its public/managed profile — display name, slug, bio/statement, contact, links, avatar, and location — linked to a Django auth user.
- `artwork-catalog`: the Artwork entity and its attributes — one or more images (with a primary), medium, dimensions, year, description, price + currency, availability status, tags — owned by an artist.
- `curation-workflow`: the moderation state machine that gates public visibility, plus the review queue, approve/reject-with-notes actions, and the featured flag.
- `public-showcase`: the visitor-facing pages — home identity, gallery/browse, artwork detail (price + inquire), artist profile, browse-by-location section, and inquiry submission.
- `management-dashboard`: the authenticated dashboard for artists (own content) and curators/admins (all content + curation actions + inquiries), with role-based access.

### Modified Capabilities
- None — this is greenfield; `openspec/specs/` is currently empty.

## Impact

- **Backend (`geodjango/world`)**: new models (`Artist`, `Artwork`, `ArtworkImage`, `Inquiry`) plus moderation fields; migrations; image upload handling via `Pillow`; new views/URLs for the showcase and the dashboard; Django groups/permissions for the `Artist` and `Curator` roles.
- **Frontend**: new Django templates (home, gallery, artwork detail, artist profile, dashboard screens) and Bootstrap styling; replaces `world/templates/index.html`.
- **Infra**: user-uploaded media (`MEDIA_ROOT`) needs persistence — a named volume in the Docker setup (`docker-compose*.yml`), and object storage (`django-storages`/S3) is a likely follow-up. PostGIS is reused for optional artist/artwork location points.
- **Auth**: artists are auth users with a linked `Artist` profile; curators/admins are assigned via groups. Account creation method (invite vs self-signup) is an open question (see design).
- **SEO**: the home page must carry clear, indexable copy/metadata reflecting the curated-local-artists identity (the repo already has prior SEO work and an `seo-audit` skill).

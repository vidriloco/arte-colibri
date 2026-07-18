## Context

Artist-uploaded images live in two places today:

- `ArtworkImage` (`world/models/artwork.py`) — `image` and `thumbnail` `ImageField`s
  (`upload_to="artworks/…"`), plus an `external_url` `URLField` already used by seed/demo
  rows that point at a remote image instead of an uploaded file.
- `Artist.avatar` (`world/models/artist.py`) — an `ImageField` (`upload_to="artists/avatars/"`).

Uploads flow through DRF dashboard endpoints and `world/imaging.py`
(`validate_image` = Pillow verify + max-4000px dimension; `make_thumbnail` = 600×750 JPEG).
Files are written to the local `MEDIA_ROOT`, which in Docker is a single named `media`
volume. There is **no byte-size cap** on uploads today.

The sibling **Inburgering** project (`web/geodjango/world/utils/s3.py`) already talks to
the same AWS account with a direct-`boto3` pattern: a `_get_s3_client()` built from
`AWS_*` settings, deterministic object keys, `put_object`, public-URL construction
(`https://{bucket}.s3.{region}.amazonaws.com/{key}`), delete-by-key and delete-by-URL,
and a `validate_image_file(content_type + size ceiling)`. It stores the resulting **public
URL** in the DB rather than using Django's storage backend. This change adopts that proven
pattern for Arte Colibrí.

## Goals / Non-Goals

**Goals:**
- Store all *new* artist-uploaded images (artwork images + thumbnails, artist avatars) in
  the existing AWS S3 bucket, addressed by a public URL persisted in the DB.
- Enforce hard per-type upload size limits — **avatar ≤ 200 KB**, **artwork image ≤ 500 KB**
  — rejected with a 400 before any object is stored.
- Reuse Inburgering's direct-`boto3` approach so the two codebases stay consistent and the
  same IAM identity/bucket conventions apply.
- Keep the public API response shapes stable (images/avatars are already exposed as
  absolute URLs), so the SPA needs no data-model changes.

**Non-Goals:**
- Migrating the *existing* local `media` volume contents into S3 (a follow-up; seed/demo
  rows already use `external_url` and are unaffected).
- Private objects / presigned URLs / CDN in front of S3 (objects are public, matching
  Inburgering; CDN is a later optimization).
- Client-side resizing/compression in the SPA to meet the size limits (the API enforces
  the limit; UX for hitting it is a frontend follow-up).
- Changing the curation/approval workflow or who owns which artwork.

## Decisions

### D1. Direct `boto3` service module over `django-storages`

Add `world/utils/s3.py` (a trimmed port of Inburgering's) exposing `_get_s3_client()`,
`_get_public_url(key)`, `put_bytes_to_s3(body, key, content_type)`, and
`delete_from_s3_by_url(url)`, plus Arte-Colibrí key derivation.

- **Why not `django-storages` + `S3Boto3Storage`?** It would make `ImageField` write to S3
  transparently, but it hides the key layout, complicates the size-limit + thumbnail flow,
  and diverges from the pattern the team already operates in Inburgering. Direct `boto3`
  keeps storage explicit and the two projects aligned.
- Store the resulting **public URL** in the DB; do not keep a local `FileField` pointer.

### D2. Persist S3 URLs on existing fields; retire local `ImageField` storage

- **Artwork:** write the uploaded image's S3 URL to `ArtworkImage.external_url` and add a
  sibling `thumbnail_url` (or reuse a thumb URL field) — the serializer
  (`ArtworkImageSerializer.get_url/get_thumb`) already prefers `external_url`, so read-side
  behavior is unchanged. The `image`/`thumbnail` `ImageField`s are deprecated for new
  uploads (left nullable for backward compatibility / migration window).
- **Artist:** replace `avatar` `ImageField` with an `avatar_url` `URLField` (or repoint the
  serializer to a stored URL). A migration copies nothing (new uploads only) but adds the
  field; `get_avatar` returns the stored URL directly.
- **Alternative considered:** keep `ImageField` and only swap the storage backend — rejected
  per D1.

### D3. Deterministic, collision-safe S3 keys

- Avatars: `artists/avatars/<artist_slug>-<artist_id>.<ext>` (one canonical object per
  artist; replacing an avatar overwrites/replaces and deletes the prior key).
- Artwork images: `artworks/<artwork_slug>/<image_id>.<ext>` and thumbnails under
  `artworks/<artwork_slug>/thumbs/<image_id>.jpg`. Because `ArtworkImage.id` is only known
  after the row exists, create the row first, then upload under its id.
- Slugs are already URL-safe (`SlugField`); still sanitize to `[a-z0-9-]` defensively as
  Inburgering does.

### D4. Size limits live in `imaging.py`, enforced pre-store

Extend validation with an explicit byte ceiling parameter:

- `validate_image(file, max_bytes)` — runs the existing Pillow verify + dimension check,
  then rejects when `file.size > max_bytes` with a clear, localizable message
  (`"Image exceeds NNN KB"`). Constants: `AVATAR_MAX_BYTES = 200 * 1024`,
  `ARTWORK_IMAGE_MAX_BYTES = 500 * 1024`.
- The limit is checked on the **uploaded original** before thumbnail generation or any S3
  call, so an oversized upload never touches the bucket. The generated thumbnail is not
  size-limited (it is always small).
- Endpoints return **HTTP 400** with a field error (`{"image": "…"}` / `{"avatar": "…"}`).

### D5. Endpoints — thin actions over the service

- `POST /api/dashboard/artworks/{id}/images/` → validate (≤ 500 KB) → create `ArtworkImage`
  row → build thumbnail → upload original + thumb to S3 → persist URLs → 201 with the
  serialized image.
- `DELETE /api/dashboard/artworks/{id}/images/{image_id}/` → delete both S3 objects
  (best-effort) → delete row → reassign primary if needed.
- `POST /api/dashboard/artworks/{id}/images/reorder/` → unchanged (position/primary only).
- `POST /api/dashboard/artist/avatar/` (or `PATCH …/artist/`) → validate (≤ 200 KB) →
  upload → persist `avatar_url` → 200 with the serialized artist. Ownership: the caller
  must own the artist profile / artwork (existing dashboard permission classes).

### D6. Configuration and failure mode

- Settings read `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_S3_REGION`
  (default `us-east-2`), `AWS_S3_BUCKET_NAME` (default `arte-colibri`) from the
  environment; add `boto3` to `requirements.txt`.
- If credentials are missing, `_get_s3_client()` raises `RuntimeError`; the upload endpoint
  surfaces this as a 503/500-class error rather than silently writing to local disk. Tests
  mock the S3 client so no live bucket is needed.

## Risks / Trade-offs

- **Public objects leak by URL** → acceptable: all images shown here are public showcase
  content; keys are unguessable enough for drafts but not secret. Revisit with presigned
  URLs if private drafts are ever needed.
- **Two-step create (row then upload) can orphan a row if S3 fails** → wrap upload in the
  request; on S3 failure delete the just-created row and return an error, so no dangling
  image without an object.
- **Deprecated `ImageField`s linger** → keep them nullable and stop writing them; a
  follow-up migration can drop them once the local `media` volume is retired.
- **Size limits may reject legitimate large photos** → 200/500 KB are product requirements;
  mitigation is a frontend hint to compress/resize before upload (out of scope here).
- **Best-effort S3 delete may leave orphaned objects** → log failures (as Inburgering
  does); deterministic keys make later cleanup scriptable.

## Migration Plan

1. Add `boto3` + AWS settings; deploy with env vars set (dev can point at the same bucket
   under a `dev/` key prefix if desired).
2. Ship the model migration (add `avatar_url` / `thumbnail_url`; keep old fields nullable).
3. New uploads go to S3 immediately. Existing local-`media` images keep rendering from
   `/media/` until a follow-up backfill copies them to S3 and repoints the URLs.
4. **Rollback:** revert the endpoints to write `ImageField`s again; already-uploaded S3
   URLs remain valid (public), so no data loss — only new uploads change destination.

## Open Questions

- Images use a **dedicated `arte-colibri` bucket** (separate from Inburgering's
  `inburgering-app`), so no key prefix is needed for isolation. Keys start at
  `artists/…` / `artworks/…`. Dev/staging can optionally point at the same bucket under
  an `env/dev/` prefix if we want isolation later.
- Do we backfill existing local images now or defer? (Assumed: defer to a follow-up.)

## Why

Artist-uploaded images (artwork photos and profile avatars) are currently written to
the Django app's local filesystem under `MEDIA_ROOT`, backed by a single Docker `media`
volume. That does not survive multi-replica or ephemeral hosting, couples image delivery
to the app process, and imposes no upper bound on upload size — a single large photo can
bloat the volume and slow every page that renders it. The project already owns an AWS S3
bucket and has a proven, direct-`boto3` integration pattern in the sibling Inburgering
project. This change moves image storage to that bucket and enforces per-type size limits.

## What Changes

- **BREAKING (storage backend):** Artist-uploaded images are stored in **AWS S3** instead
  of the local `media` volume. Uploaded objects are written under deterministic keys and
  served from **public S3 URLs**; the URL is persisted in the database. New uploads no
  longer land in `MEDIA_ROOT`.
- Add an **S3 image-storage service** in the `world` app (mirroring Inburgering's
  `world/utils/s3.py`): a `boto3` client built from settings, deterministic key
  derivation per image type, public-URL construction, upload, and delete-by-URL.
- Enforce **hard byte-size limits** on upload, rejected with a 400 before anything is
  stored: **artist profile avatar ≤ 200 KB**, **artwork image ≤ 500 KB**. Non-image and
  oversized uploads are rejected with a clear validation error.
- **Endpoints (Django REST Framework, dashboard/artist-owned):**
  - `POST /api/dashboard/artworks/{id}/images/` — upload an artwork image (≤ 500 KB).
  - `DELETE /api/dashboard/artworks/{id}/images/{image_id}/` — delete an artwork image
    (also removes the S3 objects).
  - `POST /api/dashboard/artworks/{id}/images/reorder/` — reorder / set primary
    (unchanged contract; storage-agnostic).
  - `PATCH /api/dashboard/artist/…` **and** a dedicated `POST …/avatar/` action —
    upload/replace the artist avatar (≤ 200 KB).
- Persist S3 public URLs on the existing model fields: reuse `ArtworkImage.external_url`
  for the artwork image + generated thumbnail URLs, and store the avatar URL on `Artist`.
  Local `ImageField` storage is retired for these fields.
- Add **`boto3`** to `requirements.txt` and **AWS settings** (`AWS_ACCESS_KEY_ID`,
  `AWS_SECRET_ACCESS_KEY`, `AWS_S3_REGION`, `AWS_S3_BUCKET_NAME`) read from the
  environment. When S3 is not configured, uploads fail fast with a clear error.

## Capabilities

### New Capabilities
- `image-storage`: how artist-uploaded images (artwork images + thumbnails and artist
  avatars) are validated, size-limited, stored on AWS S3, addressed by public URL, and
  deleted — plus the upload/delete/reorder API endpoints and their ownership rules.

### Modified Capabilities
<!-- None: prior changes' specs live only inside their own change folders; there is no
     baselined artwork/artist spec under openspec/specs/ whose requirements change here.
     This change introduces image storage as a distinct capability. -->

## Impact

- **Code:** `geodjango/world/` — new `utils/s3.py` (or `s3_storage.py`); `imaging.py`
  (add size limits); `api/views.py` (artwork image actions + new avatar action);
  `api/serializers.py` (avatar/image serialization now reads stored URLs); `models/`
  (avatar → URL field; artwork image URL persistence via `external_url`); a data
  migration for any schema field change.
- **APIs:** artwork image upload/delete/reorder and artist avatar upload endpoints under
  `/api/dashboard/`.
- **Dependencies:** adds `boto3`. Requires an AWS IAM identity with `s3:PutObject` /
  `s3:DeleteObject` on the configured bucket, and the bucket/objects readable publicly.
- **Config/Ops:** new required env vars for AWS credentials/region/bucket; the local
  `media` Docker volume is no longer the source of truth for new uploads (existing files
  may be migrated as a follow-up).
- **Frontend:** none required — image/avatar URLs are already consumed as absolute URLs;
  the SPA should surface the new size-limit validation errors.

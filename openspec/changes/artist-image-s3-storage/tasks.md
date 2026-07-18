## 1. Configuration & dependencies

- [x] 1.1 Add `boto3` to `requirements.txt`
- [x] 1.2 Add AWS settings to `geodjango/geodjango/settings.py` — read `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_S3_REGION` (default `us-east-2`), `AWS_S3_BUCKET_NAME` (default `arte-colibri`) from env; document the required env vars in `.env`/README and the Docker compose files

## 2. S3 service module

- [x] 2.1 Add `geodjango/world/utils/s3.py` (port of Inburgering's): `_get_s3_client()` from settings (raises `RuntimeError` when unconfigured), `_get_public_url(key)`, `put_bytes_to_s3(body, key, content_type)`, `delete_from_s3(key)`, `delete_from_s3_by_url(url)`
- [x] 2.2 Add Arte-Colibrí key derivation: `avatar_key(artist)` → `artists/avatars/<slug>-<id>.<ext>`; `artwork_image_key(image)` / `artwork_thumb_key(image)` → `artworks/<slug>/[thumbs/]<image_id>.<ext>`; sanitize slugs to `[a-z0-9-]`

## 3. Size-limited image validation

- [x] 3.1 Extend `geodjango/world/imaging.py` `validate_image(file, max_bytes=None)` to reject `file.size > max_bytes` with a clear "Image exceeds NNN KB" `ValueError` after the existing Pillow verify + dimension check
- [x] 3.2 Add constants `AVATAR_MAX_BYTES = 200 * 1024` and `ARTWORK_IMAGE_MAX_BYTES = 500 * 1024`

## 4. Data model & migration

- [x] 4.1 `Artist`: add `avatar_url` (`URLField`, blank) and repoint avatar reads to it; keep `avatar` `ImageField` nullable for backward compatibility
- [x] 4.2 `ArtworkImage`: add `thumbnail_url` (`URLField`, blank); reuse `external_url` for the stored original S3 URL; keep `image`/`thumbnail` `ImageField`s nullable
- [x] 4.3 Generate and check in the migration; verify `makemigrations --check` is clean

## 5. Artwork image endpoints (`world/api/views.py`)

- [x] 5.1 `POST …/artworks/{id}/images/` — validate `≤ ARTWORK_IMAGE_MAX_BYTES` + valid image → create `ArtworkImage` row → `make_thumbnail` → upload original + thumb to S3 → persist `external_url`/`thumbnail_url` → 201 serialized image; on S3 failure delete the just-created row and return an error
- [x] 5.2 First-image-becomes-primary preserved; ownership enforced (owner/admin/curator only, else 403/401)
- [x] 5.3 `DELETE …/artworks/{id}/images/{image_id}/` — delete original + thumb S3 objects (best-effort, tolerate missing) → delete row → promote next-by-position to primary
- [x] 5.4 `POST …/artworks/{id}/images/reorder/` — confirm still storage-agnostic (position/primary only), no change needed beyond a regression test

## 6. Artist avatar endpoint

- [x] 6.1 Add `POST …/dashboard/artist/avatar/` action — validate `≤ AVATAR_MAX_BYTES` + valid image → upload to S3 → persist `avatar_url` → 200 serialized artist; ownership enforced (owner/admin/curator only, else 403/401)
- [x] 6.2 Update `DashboardArtistSerializer` avatar handling so avatar reads return the stored S3 URL; ensure the plain artist `PATCH` no longer writes local `ImageField`

## 7. Serializers

- [x] 7.1 `ArtworkImageSerializer` — confirm `get_url`/`get_thumb` return the stored S3 URLs (prefer `external_url`/`thumbnail_url`)
- [x] 7.2 `ArtistSerializer.get_avatar` / dashboard serializer — return `avatar_url`

## 8. Tests

- [x] 8.1 Avatar: ≤ 200 KB accepted; > 200 KB rejected 400 with limit message; non-image rejected (mock S3 client)
- [x] 8.2 Artwork image: ≤ 500 KB accepted; > 500 KB rejected 400; non-image rejected; first image primary; oversized/invalid never calls `put_object`
- [x] 8.3 Ownership: non-owner upload/delete rejected 403/401 for both artwork images and avatar
- [x] 8.4 Delete removes both S3 objects (assert delete calls) and tolerates an already-missing object; primary reassigned
- [x] 8.5 S3-unconfigured upload surfaces a server error and writes nothing locally

## 9. Docs

- [x] 9.1 README/dev notes: required AWS env vars, bucket/IAM expectations (`s3:PutObject`/`s3:DeleteObject`, public-read objects), the key layout/prefix, and the 200 KB / 500 KB limits
- [x] 9.2 Note the deferred follow-ups: backfilling existing local `media` images to S3 and dropping the deprecated `ImageField`s

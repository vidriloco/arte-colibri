"""AWS S3 storage for artist-uploaded images.

A direct-``boto3`` service (no django-storages) mirroring the sibling Inburgering
project's ``world/utils/s3.py``: a client built from Django settings, deterministic
object keys, public-URL construction, upload, and delete-by-key/by-url. Uploaded
objects are public-read; their URL is what we persist on the model.

Artist-uploaded images live under two key namespaces in the ``arte-colibri`` bucket:

    artists/avatars/<artist-slug>-<artist-id>.<ext>
    artworks/<artwork-slug>/<image-id>.<ext>
    artworks/<artwork-slug>/thumbs/<image-id>.jpg
"""

import logging
import os
import re

from django.conf import settings

logger = logging.getLogger(__name__)

# Content-type → file extension for the image formats we accept.
ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


def _get_s3_client():
    """Build a boto3 S3 client from settings.

    Raises RuntimeError when credentials are not configured — callers surface
    this as a server error rather than silently writing to local disk.
    """
    import boto3

    access_key = getattr(settings, "AWS_ACCESS_KEY_ID", None)
    secret_key = getattr(settings, "AWS_SECRET_ACCESS_KEY", None)
    region = getattr(settings, "AWS_S3_REGION", "us-east-2")

    if not access_key or not secret_key:
        raise RuntimeError(
            "AWS S3 is not configured. Set AWS_ACCESS_KEY_ID and "
            "AWS_SECRET_ACCESS_KEY in the environment."
        )

    return boto3.client(
        "s3",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
    )


def _bucket():
    return getattr(settings, "AWS_S3_BUCKET_NAME", "arte-colibri")


def public_url(s3_key):
    """Public URL for an object key in the configured bucket/region."""
    bucket = _bucket()
    region = getattr(settings, "AWS_S3_REGION", "us-east-2")
    return f"https://{bucket}.s3.{region}.amazonaws.com/{s3_key}"


def _slugify(value):
    """Lowercase and reduce to ``[a-z0-9-]`` for safe use inside an S3 key."""
    value = (value or "").lower().replace(" ", "-")
    value = re.sub(r"[^a-z0-9-]", "-", value)
    return re.sub(r"-+", "-", value).strip("-")


def _ext_for(uploaded_file, content_type=None, default=".jpg"):
    """Resolve a file extension from content type, then filename, else default."""
    ct = content_type or getattr(uploaded_file, "content_type", "") or ""
    ext = ALLOWED_IMAGE_TYPES.get(ct)
    if ext:
        return ext
    name = getattr(uploaded_file, "name", "") or ""
    _, ext = os.path.splitext(name)
    return ext.lower() if ext else default


# ── Key derivation ────────────────────────────────────────────────────────────
def avatar_key(artist, uploaded_file=None, content_type=None):
    """Canonical S3 key for an artist's avatar (one object per artist)."""
    ext = _ext_for(uploaded_file, content_type) if uploaded_file else ".jpg"
    return f"artists/avatars/{_slugify(artist.slug)}-{artist.id}{ext}"


def artwork_image_key(image, uploaded_file=None, content_type=None):
    """Canonical S3 key for an artwork image, namespaced by the artwork slug."""
    ext = _ext_for(uploaded_file, content_type) if uploaded_file else ".jpg"
    slug = _slugify(image.artwork.slug)
    return f"artworks/{slug}/{image.id}{ext}"


def artwork_thumb_key(image):
    """Canonical S3 key for an artwork image's JPEG thumbnail."""
    slug = _slugify(image.artwork.slug)
    return f"artworks/{slug}/thumbs/{image.id}.jpg"


# ── Upload / delete ───────────────────────────────────────────────────────────
def put_bytes_to_s3(body, s3_key, content_type="application/octet-stream"):
    """Upload raw bytes to S3 (public-read) and return the object's public URL."""
    client = _get_s3_client()
    client.put_object(
        Bucket=_bucket(),
        Key=s3_key,
        Body=body,
        ContentType=content_type,
    )
    url = public_url(s3_key)
    logger.info("Uploaded object to S3: %s", url)
    return url


def upload_fileobj(uploaded_file, s3_key, content_type=None):
    """Upload a Django UploadedFile / file-like object and return its public URL."""
    ct = content_type or getattr(uploaded_file, "content_type", None) or "image/jpeg"
    if hasattr(uploaded_file, "seek"):
        uploaded_file.seek(0)
    body = uploaded_file.read() if hasattr(uploaded_file, "read") else uploaded_file
    return put_bytes_to_s3(body, s3_key, content_type=ct)


def delete_from_s3(s3_key):
    """Best-effort delete of an object by key. Returns True on success."""
    try:
        client = _get_s3_client()
        client.delete_object(Bucket=_bucket(), Key=s3_key)
        return True
    except Exception as exc:  # noqa: BLE001 — deletion is best-effort
        logger.error("Failed to delete S3 object %s: %s", s3_key, exc)
        return False


def delete_from_s3_by_url(url):
    """Best-effort delete of an object given its full public URL."""
    if not url:
        return False
    parts = url.split(".amazonaws.com/")
    if len(parts) != 2 or not parts[1]:
        logger.warning("Could not parse S3 key from URL: %s", url)
        return False
    return delete_from_s3(parts[1])

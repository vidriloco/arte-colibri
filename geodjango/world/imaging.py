"""Image validation + thumbnail generation (Pillow)."""

import io

from django.core.files.base import ContentFile
from PIL import Image, UnidentifiedImageError

THUMB_SIZE = (600, 750)
MAX_DIMENSION = 4000

# Per-type upload byte ceilings, enforced before anything is stored on S3.
AVATAR_MAX_BYTES = 200 * 1024  # 200 KB — artist profile avatar
ARTWORK_IMAGE_MAX_BYTES = 500 * 1024  # 500 KB — artwork image


def validate_image(django_file, max_bytes=None):
    """Raise ValueError if the upload is not a usable image.

    When ``max_bytes`` is given, the uploaded file size is checked first so an
    oversized upload is rejected before it is decoded or stored.
    """
    if max_bytes is not None:
        size = getattr(django_file, "size", None)
        if size is not None and size > max_bytes:
            raise ValueError(
                f"Image exceeds {max_bytes // 1024} KB "
                f"(got {size / 1024:.0f} KB)."
            )
    try:
        img = Image.open(django_file)
        img.verify()
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError):
        # Pillow raises SyntaxError on corrupt PNG/GIF headers.
        raise ValueError("Uploaded file is not a valid image.")
    finally:
        django_file.seek(0)
    if img.width > MAX_DIMENSION or img.height > MAX_DIMENSION:
        raise ValueError("Image is too large.")
    return True


def make_thumbnail(django_file, name="thumb.jpg"):
    """Return a ContentFile holding a JPEG thumbnail of the given image."""
    django_file.seek(0)
    img = Image.open(django_file)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    img.thumbnail(THUMB_SIZE)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=82)
    django_file.seek(0)
    return ContentFile(buf.getvalue(), name=name)

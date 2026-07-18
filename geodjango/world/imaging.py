"""Image validation + thumbnail generation (Pillow)."""

import io

from django.core.files.base import ContentFile
from PIL import Image, UnidentifiedImageError

THUMB_SIZE = (600, 750)
MAX_DIMENSION = 4000


def validate_image(django_file):
    """Raise ValueError if the upload is not a usable image."""
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

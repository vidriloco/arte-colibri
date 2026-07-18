"""Image validation + thumbnail generation (Pillow)."""

import io

from django.core.files.base import ContentFile
from PIL import Image, UnidentifiedImageError

THUMB_SIZE = (600, 750)
MAX_DIMENSION = 4000

# Compression targets: uploads are re-encoded as JPEG down to at most this size
# (they are resized/recompressed to fit, not rejected).
AVATAR_MAX_BYTES = 200 * 1024  # 200 KB — artist profile avatar
ARTWORK_IMAGE_MAX_BYTES = 700 * 1024  # 700 KB — artwork image
# Hard ceiling on the *raw* upload we'll accept before compressing.
UPLOAD_MAX_BYTES = 12 * 1024 * 1024  # 12 MB
# Longest side we keep before compressing (downscaled past this).
COMPRESS_MAX_DIMENSION = 2400


def validate_image(django_file, max_bytes=None, check_dimension=True):
    """Raise ValueError if the upload is not a usable image.

    When ``max_bytes`` is given, the uploaded file size is checked first so an
    oversized upload is rejected before it is decoded. ``check_dimension`` can be
    disabled for the compress path (which downscales instead of rejecting).
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
    if check_dimension and (img.width > MAX_DIMENSION or img.height > MAX_DIMENSION):
        raise ValueError("Image is too large.")
    return True


def compress_to_jpeg(django_file, max_bytes, name="image.jpg",
                     max_dimension=COMPRESS_MAX_DIMENSION):
    """Re-encode an uploaded image as a JPEG no larger than ``max_bytes``.

    Caps the longest side, then steps quality down and finally downscales until
    the encoded size fits. Returns a ContentFile of JPEG bytes.
    """
    django_file.seek(0)
    img = Image.open(django_file)
    if img.mode != "RGB":
        img = img.convert("RGB")  # JPEG has no alpha channel
    if max(img.size) > max_dimension:
        img.thumbnail((max_dimension, max_dimension))

    def encode(quality):
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        return buf.getvalue()

    quality = 90
    data = encode(quality)
    # Lower quality first (cheap), down to a floor.
    while len(data) > max_bytes and quality > 40:
        quality -= 10
        data = encode(quality)
    # Still too big → shrink dimensions in steps until it fits (or gets tiny).
    while len(data) > max_bytes and max(img.size) > 400:
        img = img.resize((max(1, int(img.width * 0.85)), max(1, int(img.height * 0.85))))
        data = encode(quality)

    django_file.seek(0)
    return ContentFile(data, name=name)


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

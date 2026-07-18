"""Curator-managed SEO metadata for the main public pages.

Unlike artists/artworks, SEO is operational config a curator edits directly, so
`PageSeo` is NOT a `ModeratedModel` — there is no draft/submit/approve cycle.

Resolution: the effective value of a field for a page key is taken from the page's
own row, else the `default` row, else a built-in site default. This is what both the
server-side shell injection and the public resolve endpoint call.
"""

from django.conf import settings
from django.db import models


class PageKey(models.TextChoices):
    DEFAULT = "default", "Site default"
    HOME = "home", "Home"
    GALLERY = "gallery", "Gallery"
    ARTISTS = "artists", "Artists"
    LOCATIONS = "locations", "Browse by location"


class RobotsDirective(models.TextChoices):
    INDEX = "index,follow", "Index, follow"
    NOINDEX = "noindex,follow", "No index, follow"
    NOFOLLOW = "index,nofollow", "Index, no follow"
    NONE = "noindex,nofollow", "No index, no follow"


# Every key that gets an editable dashboard slot (the `default` first).
EDITABLE_KEYS = [
    PageKey.DEFAULT,
    PageKey.HOME,
    PageKey.GALLERY,
    PageKey.ARTISTS,
    PageKey.LOCATIONS,
]

# Last-resort defaults when neither the page row nor the `default` row has a value.
# Spanish-first, mirroring the shell's original static tags.
SITE_DEFAULTS = {
    "title_es": "Arte Colibrí — Arte curado de artistas locales",
    "title_en": "Arte Colibrí — Curated art from local artists",
    "description_es": (
        "Una galería digital de arte curado de artistas locales de la Ciudad de "
        "México. Descubre y consulta obra original."
    ),
    "description_en": (
        "A digital gallery of curated art from local artists in Mexico City. "
        "Discover and inquire about original work."
    ),
}


class PageSeo(models.Model):
    key = models.CharField(max_length=20, choices=PageKey.choices, unique=True)

    title_es = models.CharField(max_length=200, blank=True, default="")
    title_en = models.CharField(max_length=200, blank=True, default="")
    description_es = models.TextField(blank=True, default="")
    description_en = models.TextField(blank=True, default="")

    og_title_es = models.CharField(max_length=200, blank=True, default="")
    og_title_en = models.CharField(max_length=200, blank=True, default="")
    og_description_es = models.TextField(blank=True, default="")
    og_description_en = models.TextField(blank=True, default="")
    og_image = models.ImageField(upload_to="seo/", blank=True, null=True)
    # Alt text describing the share image (og:image:alt / twitter:image:alt).
    image_alt_es = models.CharField(max_length=250, blank=True, default="")
    image_alt_en = models.CharField(max_length=250, blank=True, default="")

    # Comma-separated meta keywords (name="keywords").
    keywords_es = models.CharField(max_length=300, blank=True, default="")
    keywords_en = models.CharField(max_length=300, blank=True, default="")

    canonical = models.URLField(blank=True, default="")
    robots = models.CharField(
        max_length=20, choices=RobotsDirective.choices, default=RobotsDirective.INDEX
    )

    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        ordering = ["key"]
        verbose_name = "Page SEO"
        verbose_name_plural = "Page SEO"

    def __str__(self):
        return self.get_key_display()

    @classmethod
    def resolve(cls, key):
        """Effective SEO for `key` as a dict of bilingual pairs + flat values.

        Per-field fallback: page row -> `default` row -> `SITE_DEFAULTS`. OG
        title/description fall back to the plain title/description of the same
        resolution. `og_image` is returned as a FieldFile (or None).
        """
        rows = {
            r.key: r
            for r in cls.objects.filter(key__in=[str(key), PageKey.DEFAULT])
        }
        page = rows.get(str(key))
        default = rows.get(PageKey.DEFAULT)
        sources = [s for s in (page, default) if s is not None]

        def pick(field):
            for src in sources:
                val = getattr(src, field, "") or ""
                if val != "":
                    return val
            return SITE_DEFAULTS.get(field, "")

        og_image = None
        for src in sources:
            if getattr(src, "og_image", None):
                og_image = src.og_image
                break

        title = {"es": pick("title_es"), "en": pick("title_en")}
        description = {"es": pick("description_es"), "en": pick("description_en")}
        og_title = {
            "es": pick("og_title_es") or title["es"],
            "en": pick("og_title_en") or title["en"],
        }
        og_description = {
            "es": pick("og_description_es") or description["es"],
            "en": pick("og_description_en") or description["en"],
        }
        # Alt/keywords stand on their own — no fallback to title/description.
        image_alt = {"es": pick("image_alt_es"), "en": pick("image_alt_en")}
        keywords = {"es": pick("keywords_es"), "en": pick("keywords_en")}
        return {
            "title": title,
            "description": description,
            "og_title": og_title,
            "og_description": og_description,
            "og_image": og_image,
            "image_alt": image_alt,
            "keywords": keywords,
            "canonical": pick("canonical"),
            "robots": pick("robots") or RobotsDirective.INDEX.value,
        }

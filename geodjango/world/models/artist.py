"""Artist profile — a moderated profile linked one-to-one to an auth user."""

from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.db import models

from .moderation import ModeratedModel


class Artist(ModeratedModel):
    """An artist's public/managed profile, owned by one auth user."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="artist_profile",
    )
    slug = models.SlugField(max_length=140, unique=True)
    display_name = models.CharField(max_length=160)

    discipline_es = models.CharField(max_length=80, blank=True, default="")
    discipline_en = models.CharField(max_length=80, blank=True, default="")

    bio_es = models.TextField(blank=True, default="")
    bio_en = models.TextField(blank=True, default="")

    city = models.CharField(max_length=120, blank=True, default="")
    region = models.ForeignKey(
        "world.Region",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="artists",
    )
    point = gis_models.PointField(null=True, blank=True, srid=4326)

    instagram = models.CharField(max_length=120, blank=True, default="")
    web = models.CharField(max_length=200, blank=True, default="")

    avatar = models.ImageField(upload_to="artists/avatars/", null=True, blank=True)
    since = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["display_name"]

    def __str__(self):
        return self.display_name

    @property
    def initials(self):
        parts = [p for p in self.display_name.split() if p]
        return "".join(p[0] for p in parts[:2]).upper()

    def published_works(self):
        return self.artworks.published().order_by("-year", "-created_at")

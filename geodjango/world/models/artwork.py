"""Artwork catalog + per-artwork images."""

from django.db import models

from .moderation import (
    ModeratedModel,
    ModeratedQuerySet,
    ModerationStatus,
)


class Availability(models.TextChoices):
    AVAILABLE = "available", "Available"
    SOLD = "sold", "Sold"
    NFS = "nfs", "Not for sale"


class ArtworkQuerySet(ModeratedQuerySet):
    def public(self):
        """Published works whose artist profile is also published."""
        return self.filter(
            status=ModerationStatus.PUBLISHED,
            artist__status=ModerationStatus.PUBLISHED,
        )

    def featured(self):
        # Catalog order (mirrors the design): featured_order first, then creation.
        return self.public().filter(featured=True).order_by("featured_order", "id")

    def recent(self):
        # Newest year first; stable within a year by catalog (creation) order.
        return self.public().order_by("-year", "id")


class ArtworkManager(models.Manager.from_queryset(ArtworkQuerySet)):
    pass


class Artwork(ModeratedModel):
    artist = models.ForeignKey(
        "world.Artist",
        on_delete=models.CASCADE,
        related_name="artworks",
    )
    slug = models.SlugField(max_length=180, unique=True)

    title_es = models.CharField(max_length=200)
    title_en = models.CharField(max_length=200, blank=True, default="")
    description_es = models.TextField(blank=True, default="")
    description_en = models.TextField(blank=True, default="")
    medium_es = models.CharField(max_length=200, blank=True, default="")
    medium_en = models.CharField(max_length=200, blank=True, default="")

    dimensions = models.CharField(max_length=120, blank=True, default="")
    year = models.PositiveIntegerField(null=True, blank=True)

    price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default="MXN")
    availability = models.CharField(
        max_length=12,
        choices=Availability.choices,
        default=Availability.AVAILABLE,
    )

    tags = models.ManyToManyField("world.Tag", blank=True, related_name="artworks")

    featured = models.BooleanField(default=False)
    featured_order = models.PositiveIntegerField(null=True, blank=True)

    objects = ArtworkManager()

    class Meta:
        ordering = ["-year", "-created_at"]

    def __str__(self):
        return self.title_es

    @property
    def primary_image(self):
        return (
            self.images.filter(is_primary=True).first()
            or self.images.order_by("position", "id").first()
        )


class ArtworkImage(models.Model):
    artwork = models.ForeignKey(
        "world.Artwork",
        on_delete=models.CASCADE,
        related_name="images",
    )
    # Legacy local-filesystem fields; retained (nullable) for pre-S3 rows.
    image = models.ImageField(upload_to="artworks/", null=True, blank=True)
    thumbnail = models.ImageField(upload_to="artworks/thumbs/", null=True, blank=True)
    # Public URL of the full-size image: an uploaded S3 object, or a seed/demo
    # remote URL. Preferred by the serializer over the local `image` field.
    external_url = models.URLField(max_length=500, blank=True, default="")
    # Public S3 URL of the generated thumbnail (new uploads populate this).
    thumbnail_url = models.URLField(max_length=500, blank=True, default="")
    position = models.PositiveIntegerField(default=0)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["position", "id"]

    def __str__(self):
        return f"{self.artwork.title_es} · image {self.position}"

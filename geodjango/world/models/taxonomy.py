"""Bilingual taxonomy: regions (CDMX neighborhoods) and tags."""

from django.db import models


class Region(models.Model):
    """A CDMX area used for the secondary 'browse by location' section."""

    slug = models.SlugField(max_length=64, unique=True)
    name_es = models.CharField(max_length=120)
    name_en = models.CharField(max_length=120)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name_es"]

    def __str__(self):
        return self.name_es


class Tag(models.Model):
    """A bilingual descriptor (technique / style) attached to artworks."""

    slug = models.SlugField(max_length=64, unique=True)
    label_es = models.CharField(max_length=120)
    label_en = models.CharField(max_length=120)

    class Meta:
        ordering = ["slug"]

    def __str__(self):
        return self.label_es

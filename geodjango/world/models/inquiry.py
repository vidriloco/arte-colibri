"""Visitor inquiries about a specific published artwork (no checkout)."""

from django.db import models


class Inquiry(models.Model):
    artwork = models.ForeignKey(
        "world.Artwork",
        on_delete=models.CASCADE,
        related_name="inquiries",
    )
    name = models.CharField(max_length=160)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Inquiries"

    def __str__(self):
        return f"{self.name} → {self.artwork.title_es}"

    @property
    def artist(self):
        return self.artwork.artist

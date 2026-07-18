"""Curator-managed third-party API keys (type + secret value).

Stored in the DB so a curator can add/rotate keys without a redeploy. The raw
value is never returned by the API (see `world/api/serializers.py`); reads are
masked to a short preview. Plaintext at rest — encryption is a follow-up.
"""

from django.conf import settings
from django.db import models


class ApiType(models.TextChoices):
    OPENROUTER = "openrouter", "OpenRouter"


class ApiKey(models.Model):
    # One stored key per type — saving a type that exists replaces it.
    api_type = models.CharField(max_length=40, choices=ApiType.choices, unique=True)
    key_value = models.TextField()
    # For LLM providers (OpenRouter): which model to use. Blank → the code
    # default. Validated against the allow-list in `world/utils/openrouter.py`.
    model = models.CharField(max_length=100, blank=True, default="")

    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        ordering = ["api_type"]
        verbose_name = "API key"
        verbose_name_plural = "API keys"

    def __str__(self):
        return self.get_api_type_display()

    @property
    def preview(self):
        """A masked hint of the stored secret — never the whole thing."""
        v = self.key_value or ""
        if len(v) >= 4:
            return "…" + v[-4:]
        return "…" if v else ""

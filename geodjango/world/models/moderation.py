"""Shared moderation state machine: draft -> submitted -> published / rejected.

Only PUBLISHED content is ever publicly visible; the gate is enforced through
the `published` manager/queryset on each model, never in templates/serializers.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone


class ModerationStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    SUBMITTED = "submitted", "Submitted"
    PUBLISHED = "published", "Published"
    REJECTED = "rejected", "Rejected"


class ModeratedQuerySet(models.QuerySet):
    def published(self):
        return self.filter(status=ModerationStatus.PUBLISHED)

    def submitted(self):
        return self.filter(status=ModerationStatus.SUBMITTED)


class ModeratedManager(models.Manager.from_queryset(ModeratedQuerySet)):
    pass


class PublishedManager(models.Manager.from_queryset(ModeratedQuerySet)):
    """Default-to-published manager for public querysets."""

    def get_queryset(self):
        return super().get_queryset().filter(status=ModerationStatus.PUBLISHED)


class ModeratedModel(models.Model):
    """Abstract base adding moderation fields + transition helpers."""

    status = models.CharField(
        max_length=12,
        choices=ModerationStatus.choices,
        default=ModerationStatus.DRAFT,
        db_index=True,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ModeratedManager()
    published_objects = PublishedManager()

    class Meta:
        abstract = True

    @property
    def is_published(self):
        return self.status == ModerationStatus.PUBLISHED

    # --- transitions (validation lives in the API layer / serializers) ---
    def submit(self):
        self.status = ModerationStatus.SUBMITTED
        self.save(update_fields=["status", "updated_at"])

    def approve(self, reviewer):
        self.status = ModerationStatus.PUBLISHED
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.save(update_fields=["status", "reviewed_by", "reviewed_at", "updated_at"])

    def reject(self, reviewer, notes):
        self.status = ModerationStatus.REJECTED
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.save(
            update_fields=[
                "status",
                "reviewed_by",
                "reviewed_at",
                "review_notes",
                "updated_at",
            ]
        )

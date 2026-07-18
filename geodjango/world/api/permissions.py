"""DRF permissions reusing the Artist / Curator role groups."""

from django.conf import settings
from rest_framework import permissions


def is_curator(user):
    return bool(
        user
        and user.is_authenticated
        and (user.is_superuser or user.groups.filter(name=settings.CURATOR_GROUP).exists())
    )


class IsCurator(permissions.BasePermission):
    """Only users in the Curator group (or admins)."""

    message = "Curator access required."

    def has_permission(self, request, view):
        return is_curator(request.user)


class IsArtistOwner(permissions.BasePermission):
    """Authenticated artist; object-level check enforces ownership."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        artist = getattr(request.user, "artist_profile", None)
        if artist is None:
            return False
        # obj may be an Artwork (has .artist) or an Artist profile itself.
        owner = getattr(obj, "artist", obj)
        return owner == artist

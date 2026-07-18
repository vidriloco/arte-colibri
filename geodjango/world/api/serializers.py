"""Serializers — split by audience (public / owner / curator) to avoid leaks."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction
from django.utils.text import slugify
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from world.models import (
    Artist,
    Artwork,
    ArtworkImage,
    Availability,
    Inquiry,
    ModerationStatus,
    PageSeo,
    Region,
    Tag,
)

from .fields import BilingualField

User = get_user_model()


# ── Taxonomy ─────────────────────────────────────────────────────────────────
class TagSerializer(serializers.ModelSerializer):
    label = BilingualField("label_es", "label_en", read_only=True)

    class Meta:
        model = Tag
        fields = ["slug", "label"]


class RegionSerializer(serializers.ModelSerializer):
    name = BilingualField("name_es", "name_en", read_only=True)

    class Meta:
        model = Region
        fields = ["slug", "name"]


# ── Images ───────────────────────────────────────────────────────────────────
class ArtworkImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    thumb = serializers.SerializerMethodField()

    class Meta:
        model = ArtworkImage
        fields = ["id", "url", "thumb", "position", "is_primary"]

    def _abs(self, f):
        if not f:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(f.url) if request else f.url

    def get_url(self, obj):
        return obj.external_url or self._abs(obj.image)

    def get_thumb(self, obj):
        return obj.external_url or self._abs(obj.thumbnail) or self._abs(obj.image)


# ── Public artwork (read-only) ────────────────────────────────────────────────
class ArtworkListSerializer(serializers.ModelSerializer):
    title = BilingualField("title_es", "title_en", read_only=True)
    medium = BilingualField("medium_es", "medium_en", read_only=True)
    artist_name = serializers.CharField(source="artist.display_name", read_only=True)
    artist_slug = serializers.SlugField(source="artist.slug", read_only=True)
    primary_image = serializers.SerializerMethodField()
    tags = serializers.SlugRelatedField(slug_field="slug", many=True, read_only=True)

    class Meta:
        model = Artwork
        fields = [
            "slug", "title", "year", "medium", "dimensions",
            "price", "currency", "availability", "featured",
            "artist_name", "artist_slug", "primary_image", "tags",
        ]

    def get_primary_image(self, obj):
        img = obj.primary_image
        if not img:
            return None
        return ArtworkImageSerializer(img, context=self.context).data


class ArtworkDetailSerializer(ArtworkListSerializer):
    description = BilingualField("description_es", "description_en", read_only=True)
    images = ArtworkImageSerializer(many=True, read_only=True)
    artist = serializers.SerializerMethodField()

    class Meta(ArtworkListSerializer.Meta):
        fields = ArtworkListSerializer.Meta.fields + ["description", "images", "artist"]

    def get_artist(self, obj):
        return ArtistMiniSerializer(obj.artist, context=self.context).data


# ── Public artist (read-only) ─────────────────────────────────────────────────
class ArtistMiniSerializer(serializers.ModelSerializer):
    discipline = BilingualField("discipline_es", "discipline_en", read_only=True)
    region = serializers.SlugRelatedField(slug_field="slug", read_only=True)
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = Artist
        fields = [
            "slug", "display_name", "discipline", "city", "region",
            "instagram", "web", "since", "avatar", "initials",
        ]

    def get_avatar(self, obj):
        if not obj.avatar:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.avatar.url) if request else obj.avatar.url


class ArtistListSerializer(ArtistMiniSerializer):
    """List card: identity + work count + up to 3 highlight works (roster/grid)."""

    bio = BilingualField("bio_es", "bio_en", read_only=True)
    works_count = serializers.SerializerMethodField()
    highlights = serializers.SerializerMethodField()

    class Meta(ArtistMiniSerializer.Meta):
        fields = ArtistMiniSerializer.Meta.fields + ["bio", "works_count", "highlights"]

    def get_works_count(self, obj):
        return obj.published_works().count()

    def get_highlights(self, obj):
        qs = obj.published_works()
        ranked = sorted(qs, key=lambda w: (not w.featured,))[:3]
        return ArtworkListSerializer(ranked, many=True, context=self.context).data


class ArtistDetailSerializer(ArtistMiniSerializer):
    bio = BilingualField("bio_es", "bio_en", read_only=True)
    works = serializers.SerializerMethodField()

    class Meta(ArtistMiniSerializer.Meta):
        fields = ArtistMiniSerializer.Meta.fields + ["bio", "works"]

    def get_works(self, obj):
        qs = obj.published_works()
        return ArtworkListSerializer(qs, many=True, context=self.context).data


# ── Inquiry ───────────────────────────────────────────────────────────────────
class InquiryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inquiry
        fields = ["name", "email", "message"]

    def validate_name(self, v):
        if not v.strip():
            raise serializers.ValidationError("This field is required.")
        return v


class InquirySerializer(serializers.ModelSerializer):
    artwork_title = BilingualField(
        "artwork.title_es", "artwork.title_en", read_only=True
    )
    artwork_slug = serializers.SlugField(source="artwork.slug", read_only=True)

    class Meta:
        model = Inquiry
        fields = [
            "id", "name", "email", "message", "created_at",
            "artwork_slug", "artwork_title",
        ]


# ── Owner: artwork write ──────────────────────────────────────────────────────
class ArtworkOwnerSerializer(serializers.ModelSerializer):
    title = BilingualField("title_es", "title_en")
    medium = BilingualField("medium_es", "medium_en", required=False)
    description = BilingualField("description_es", "description_en", required=False)
    tags = serializers.SlugRelatedField(
        slug_field="slug", many=True, queryset=Tag.objects.all(), required=False
    )
    images = ArtworkImageSerializer(many=True, read_only=True)
    artist_slug = serializers.SlugField(source="artist.slug", read_only=True)

    class Meta:
        model = Artwork
        fields = [
            "id", "slug", "title", "medium", "description", "dimensions",
            "year", "price", "currency", "availability", "tags",
            "status", "featured", "images", "review_notes", "artist_slug",
        ]
        read_only_fields = ["slug", "status", "featured", "review_notes"]

    def validate_availability(self, v):
        if v not in Availability.values:
            raise serializers.ValidationError("Invalid availability.")
        return v

    def _unique_slug(self, base):
        base = slugify(base) or "obra"
        slug, i = base, 2
        while Artwork.objects.filter(slug=slug).exists():
            slug = f"{base}-{i}"
            i += 1
        return slug

    def create(self, validated):
        tags = validated.pop("tags", [])
        artist = self.context["artist"]
        validated["slug"] = self._unique_slug(validated.get("title_es", "obra"))
        artwork = Artwork.objects.create(artist=artist, **validated)
        if tags:
            artwork.tags.set(tags)
        return artwork

    def update(self, instance, validated):
        tags = validated.pop("tags", None)
        for k, v in validated.items():
            setattr(instance, k, v)
        instance.save()
        if tags is not None:
            instance.tags.set(tags)
        return instance


# ── Owner: artist profile write ───────────────────────────────────────────────
class ArtistOwnerSerializer(serializers.ModelSerializer):
    discipline = BilingualField("discipline_es", "discipline_en", required=False)
    bio = BilingualField("bio_es", "bio_en", required=False)
    region = serializers.SlugRelatedField(
        slug_field="slug", queryset=Region.objects.all(),
        required=False, allow_null=True,
    )
    avatar = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Artist
        fields = [
            "slug", "display_name", "discipline", "bio", "city", "region",
            "instagram", "web", "since", "avatar", "status", "review_notes",
        ]
        read_only_fields = ["slug", "status", "review_notes"]


# ── Curation ──────────────────────────────────────────────────────────────────
class ReviewArtworkSerializer(ArtworkDetailSerializer):
    id = serializers.IntegerField(read_only=True)
    reviewed_at = serializers.DateTimeField(read_only=True)
    review_notes = serializers.CharField(read_only=True)

    class Meta(ArtworkDetailSerializer.Meta):
        fields = ArtworkDetailSerializer.Meta.fields + [
            "id", "status", "reviewed_at", "review_notes",
        ]


class ReviewArtistSerializer(ArtistDetailSerializer):
    id = serializers.IntegerField(read_only=True)

    class Meta(ArtistDetailSerializer.Meta):
        fields = ArtistDetailSerializer.Meta.fields + [
            "id", "status", "review_notes",
        ]


# ── Auth ──────────────────────────────────────────────────────────────────────
class SignupSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=160)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)

    def validate_email(self, v):
        if User.objects.filter(username__iexact=v).exists() or User.objects.filter(
            email__iexact=v
        ).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return v

    def _unique_artist_slug(self, name):
        base = slugify(name) or "artista"
        slug, i = base, 2
        while Artist.objects.filter(slug=slug).exists():
            slug = f"{base}-{i}"
            i += 1
        return slug

    @transaction.atomic
    def create(self, validated):
        from django.conf import settings as dj_settings

        name = validated["name"].strip()
        user = User.objects.create_user(
            username=validated["email"],
            email=validated["email"],
            password=validated["password"],
            first_name=name[:150],
        )
        group, _ = Group.objects.get_or_create(name=dj_settings.ARTIST_GROUP)
        user.groups.add(group)
        Artist.objects.create(
            user=user,
            display_name=name,
            slug=self._unique_artist_slug(name),
            status=ModerationStatus.DRAFT,
        )
        return user


# ── Page SEO (curator R/W) ────────────────────────────────────────────────────
class PageSeoSerializer(serializers.ModelSerializer):
    """Editable SEO slot. Bilingual pairs exposed as {es,en}; `key` is fixed."""

    key = serializers.CharField(read_only=True)
    key_label = serializers.CharField(source="get_key_display", read_only=True)
    title = BilingualField("title_es", "title_en", required=False)
    description = BilingualField("description_es", "description_en", required=False)
    og_title = BilingualField("og_title_es", "og_title_en", required=False)
    og_description = BilingualField(
        "og_description_es", "og_description_en", required=False
    )
    og_image = serializers.ImageField(read_only=True)
    og_image_url = serializers.SerializerMethodField()

    class Meta:
        model = PageSeo
        fields = [
            "key", "key_label", "title", "description",
            "og_title", "og_description", "og_image", "og_image_url",
            "canonical", "robots", "updated_at",
        ]
        read_only_fields = ["og_image", "updated_at"]

    def get_og_image_url(self, obj):
        if not obj.og_image:
            return None
        request = self.context.get("request")
        return (
            request.build_absolute_uri(obj.og_image.url)
            if request
            else obj.og_image.url
        )


class UserSerializer(serializers.Serializer):
    """Current-user payload: identity + role + linked artist (if any)."""

    id = serializers.IntegerField()
    name = serializers.SerializerMethodField()
    email = serializers.EmailField()
    role = serializers.SerializerMethodField()
    artist = serializers.SerializerMethodField()

    def get_name(self, obj):
        return (obj.get_full_name() or obj.username).strip()

    def get_role(self, obj):
        from django.conf import settings as dj_settings

        if obj.is_superuser or obj.groups.filter(name=dj_settings.CURATOR_GROUP).exists():
            return "curator"
        return "artist"

    def get_artist(self, obj):
        artist = getattr(obj, "artist_profile", None)
        if not artist:
            return None
        return ArtistOwnerSerializer(artist, context=self.context).data

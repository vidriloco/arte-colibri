"""API views: public (published-only), auth/signup, dashboard, curation."""

import logging

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from world.imaging import (
    ARTWORK_IMAGE_MAX_BYTES,
    AVATAR_MAX_BYTES,
    UPLOAD_MAX_BYTES,
    compress_to_jpeg,
    make_thumbnail,
    validate_image,
)
from world.utils import s3
from world.models import (
    ApiKey,
    ApiType,
    Artist,
    Artwork,
    ArtworkImage,
    Inquiry,
    ModerationStatus,
    PageSeo,
    Region,
    Tag,
)
from world.utils.openrouter import (
    ALLOWED_MODEL_IDS,
    DEFAULT_MODEL,
    SEO_MODELS,
    OpenRouterError,
    generate_seo,
)
from world.models.seo import EDITABLE_KEYS
from world.seo import resolve_public
from world.turnstile import check_request as check_turnstile

from .permissions import IsArtistOwner, IsCurator, is_curator
from .serializers import (
    AdminArtistSerializer,
    ArtistDetailSerializer,
    ArtistListSerializer,
    ArtistMiniSerializer,
    ArtistOwnerSerializer,
    ArtworkDetailSerializer,
    ArtworkImageSerializer,
    ArtworkListSerializer,
    ArtworkOwnerSerializer,
    InquiryCreateSerializer,
    InquirySerializer,
    PageSeoSerializer,
    RegionSerializer,
    ReviewArtistSerializer,
    ReviewArtworkSerializer,
    SignupSerializer,
    TagSerializer,
    UserSerializer,
)

User = get_user_model()
logger = logging.getLogger(__name__)


def _upload_error_response(exc, field):
    """Map an image-upload exception to a clean, useful JSON error response."""
    if isinstance(exc, RuntimeError):
        logger.warning("%s upload failed (storage not configured): %s", field, exc)
        return Response(
            {field: "Image storage isn't set up on the server yet. Contact the administrator."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    logger.exception("%s upload failed", field)
    return Response(
        {field: "We couldn't upload this image. Please try again, or use a different file."},
        status=status.HTTP_502_BAD_GATEWAY,
    )


# ── Public ────────────────────────────────────────────────────────────────────
class HomeView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        featured = Artwork.objects.featured()[:6]
        recent = Artwork.objects.recent()[:6]
        ctx = {"request": request}
        return Response(
            {
                # Detail serializer so the editorial hero caption has a description.
                "featured": ArtworkDetailSerializer(featured, many=True, context=ctx).data,
                "recent": ArtworkListSerializer(recent, many=True, context=ctx).data,
                "carousel": ArtworkListSerializer(
                    Artwork.objects.recent()[:5], many=True, context=ctx
                ).data,
                "stats": {
                    "artists": Artist.published_objects.count(),
                    "works": Artwork.objects.public().count(),
                    "regions": Region.objects.count(),
                },
            }
        )


class ArtworkViewSet(viewsets.ReadOnlyModelViewSet):
    """Public gallery list + detail (published-only), with filter/sort."""

    permission_classes = [AllowAny]
    lookup_field = "slug"

    def get_queryset(self):
        qs = Artwork.objects.public().select_related("artist").prefetch_related(
            "images", "tags"
        )
        tags = self.request.query_params.getlist("tag")
        for tag in tags:
            qs = qs.filter(tags__slug=tag)
        sort = self.request.query_params.get("sort", "recent")
        if sort == "price_asc":
            qs = qs.order_by("price", "-year")
        elif sort == "price_desc":
            qs = qs.order_by("-price", "-year")
        else:
            qs = qs.order_by("-year", "id")
        return qs.distinct()

    def get_serializer_class(self):
        return (
            ArtworkDetailSerializer
            if self.action == "retrieve"
            else ArtworkListSerializer
        )

    @action(detail=True, methods=["post"], permission_classes=[AllowAny])
    def inquiries(self, request, slug=None):
        artwork = self.get_object()  # 404 if not published
        check_turnstile(request)
        ser = InquiryCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save(artwork=artwork)
        return Response(
            {"detail": "Inquiry received."}, status=status.HTTP_201_CREATED
        )


class ArtistViewSet(viewsets.ReadOnlyModelViewSet):
    """Public artist list + detail (published profiles only)."""

    permission_classes = [AllowAny]
    lookup_field = "slug"

    def get_queryset(self):
        return (
            Artist.published_objects.filter(
                artworks__status=ModerationStatus.PUBLISHED
            )
            .distinct()
            .order_by("display_name")
        )

    def get_serializer_class(self):
        return (
            ArtistDetailSerializer
            if self.action == "retrieve"
            else ArtistListSerializer
        )


class LocationsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        ctx = {"request": request}
        out = []
        for region in Region.objects.all():
            works = (
                Artwork.objects.public()
                .filter(artist__region=region)
                .select_related("artist")
                .prefetch_related("images")
            )
            if not works.exists():
                continue
            out.append(
                {
                    "slug": region.slug,
                    "name": {"es": region.name_es, "en": region.name_en},
                    "count": works.count(),
                    "works": ArtworkListSerializer(works, many=True, context=ctx).data,
                }
            )
        return Response(out)


class MetaView(APIView):
    """Tags + regions that actually have published work, for filter UIs."""

    permission_classes = [AllowAny]

    def get(self, request):
        ctx = {"request": request}
        tags = Tag.objects.filter(
            artworks__status=ModerationStatus.PUBLISHED
        ).distinct()
        regions = Region.objects.filter(
            artists__artworks__status=ModerationStatus.PUBLISHED
        ).distinct()
        return Response(
            {
                "tags": TagSerializer(tags, many=True, context=ctx).data,
                "regions": RegionSerializer(regions, many=True, context=ctx).data,
                # Public site key for the SPA's Turnstile widgets; empty means
                # Turnstile is disabled and forms submit without a token.
                "turnstile_site_key": settings.TURNSTILE_SITE_KEY,
            }
        )


class PublicSeoView(APIView):
    """Resolved SEO for a page key, for the SPA's client-side head manager."""

    permission_classes = [AllowAny]

    def get(self, request):
        key = request.query_params.get("page", "default")
        return Response(resolve_public(key, request))


# ── Auth ──────────────────────────────────────────────────────────────────────
def _auth_payload(user, request):
    token, _ = Token.objects.get_or_create(user=user)
    return {
        "token": token.key,
        "user": UserSerializer(user, context={"request": request}).data,
    }


class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        check_turnstile(request)
        ser = SignupSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        return Response(_auth_payload(user, request), status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email", "")
        password = request.data.get("password", "")
        user = authenticate(username=email, password=password)
        if user is None:
            return Response(
                {"detail": "Invalid credentials."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(_auth_payload(user, request))


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user, context={"request": request}).data)


# ── Dashboard (artist, owner-scoped) ──────────────────────────────────────────
class DashboardProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def _artist(self, request):
        return get_object_or_404(Artist, user=request.user)

    def get(self, request):
        artist = self._artist(request)
        return Response(ArtistOwnerSerializer(artist, context={"request": request}).data)

    def put(self, request):
        return self._update(request)

    def patch(self, request):
        return self._update(request, partial=True)

    def _update(self, request, partial=False):
        artist = self._artist(request)
        ser = ArtistOwnerSerializer(
            artist, data=request.data, partial=partial, context={"request": request}
        )
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)

    def post(self, request):
        # submit profile for review
        artist = self._artist(request)
        artist.submit()
        return Response(ArtistOwnerSerializer(artist, context={"request": request}).data)


class DashboardAvatarView(APIView):
    """Upload/replace the signed-in artist's profile avatar (≤ 200 KB) on S3."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        artist = get_object_or_404(Artist, user=request.user)
        f = request.FILES.get("avatar") or request.FILES.get("image")
        if not f:
            return Response(
                {"avatar": "No file provided."}, status=status.HTTP_400_BAD_REQUEST
            )
        # Reject non-images / absurd uploads only; the avatar is compressed to a
        # JPEG ≤ 200 KB (resized as needed) rather than rejected merely for size.
        try:
            validate_image(f, max_bytes=UPLOAD_MAX_BYTES, check_dimension=False)
        except ValueError as e:
            return Response({"avatar": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        try:
            jpeg = compress_to_jpeg(f, max_bytes=AVATAR_MAX_BYTES, name="avatar.jpg")
            artist.avatar_url = s3.put_bytes_to_s3(
                jpeg.read(),
                s3.avatar_key(artist, content_type="image/jpeg"),
                content_type="image/jpeg",
            )
            artist.save(update_fields=["avatar_url"])
        except Exception as e:  # noqa: BLE001
            return _upload_error_response(e, "avatar")
        return Response(ArtistOwnerSerializer(artist, context={"request": request}).data)


class DashboardArtworkViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsArtistOwner]
    serializer_class = ArtworkOwnerSerializer

    def get_artist(self):
        return get_object_or_404(Artist, user=self.request.user)

    def get_queryset(self):
        return (
            Artwork.objects.filter(artist__user=self.request.user)
            .prefetch_related("images", "tags")
            .order_by("-created_at")
        )

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["artist"] = self.get_artist()
        return ctx

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        artwork = self.get_object()
        if artwork.status not in (ModerationStatus.DRAFT, ModerationStatus.REJECTED):
            return Response(
                {"detail": "Only drafts can be submitted."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        artwork.submit()
        return Response(self.get_serializer(artwork).data)

    @action(detail=True, methods=["post"], url_path="images")
    def add_image(self, request, pk=None):
        artwork = self.get_object()
        f = request.FILES.get("image")
        if not f:
            return Response(
                {"image": "No file provided."}, status=status.HTTP_400_BAD_REQUEST
            )
        # Reject non-images / absurd uploads only; the image is compressed to a
        # JPEG ≤ 700 KB (resized as needed) rather than rejected merely for size.
        try:
            validate_image(f, max_bytes=UPLOAD_MAX_BYTES, check_dimension=False)
        except ValueError as e:
            return Response({"image": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        count = artwork.images.count()
        img = ArtworkImage.objects.create(
            artwork=artwork, position=count, is_primary=(count == 0)
        )
        # Keys are namespaced by the artwork slug + the new image id, so create
        # the row first, then upload the compressed JPEG + generated thumbnail.
        try:
            jpeg = compress_to_jpeg(f, max_bytes=ARTWORK_IMAGE_MAX_BYTES, name=f"{img.id}.jpg")
            img.external_url = s3.put_bytes_to_s3(
                jpeg.read(),
                s3.artwork_image_key(img, content_type="image/jpeg"),
                content_type="image/jpeg",
            )
            thumb = make_thumbnail(f, name=f"{img.id}.jpg")
            img.thumbnail_url = s3.put_bytes_to_s3(
                thumb.read(), s3.artwork_thumb_key(img), content_type="image/jpeg"
            )
            img.save(update_fields=["external_url", "thumbnail_url"])
        except Exception as e:  # noqa: BLE001 — don't leave an image row without objects
            img.delete()
            return _upload_error_response(e, "image")
        return Response(
            ArtworkImageSerializer(img, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["delete"],
        url_path=r"images/(?P<image_id>[^/.]+)",
    )
    def delete_image(self, request, pk=None, image_id=None):
        artwork = self.get_object()
        img = get_object_or_404(ArtworkImage, pk=image_id, artwork=artwork)
        was_primary = img.is_primary
        # Best-effort removal of the S3 objects (tolerates an already-missing one).
        s3.delete_from_s3_by_url(img.external_url)
        s3.delete_from_s3_by_url(img.thumbnail_url)
        img.delete()
        if was_primary:
            nxt = artwork.images.order_by("position", "id").first()
            if nxt:
                nxt.is_primary = True
                nxt.save(update_fields=["is_primary"])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"], url_path="images/reorder")
    def reorder_images(self, request, pk=None):
        artwork = self.get_object()
        order = request.data.get("order", [])  # list of image ids in new order
        primary_id = request.data.get("primary")
        for pos, img_id in enumerate(order):
            artwork.images.filter(pk=img_id).update(position=pos)
        if primary_id is not None:
            artwork.images.update(is_primary=False)
            artwork.images.filter(pk=primary_id).update(is_primary=True)
        imgs = artwork.images.order_by("position", "id")
        return Response(
            ArtworkImageSerializer(imgs, many=True, context={"request": request}).data
        )


class DashboardInquiriesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Inquiry.objects.filter(artwork__artist__user=request.user).select_related(
            "artwork"
        )
        return Response(
            InquirySerializer(qs, many=True, context={"request": request}).data
        )


# ── Curation (curator-only) ───────────────────────────────────────────────────
class CurationQueueView(APIView):
    permission_classes = [IsAuthenticated, IsCurator]

    def get(self, request):
        ctx = {"request": request}
        artworks = Artwork.objects.filter(
            status=ModerationStatus.SUBMITTED
        ).select_related("artist").prefetch_related("images")
        artists = Artist.objects.filter(status=ModerationStatus.SUBMITTED)
        return Response(
            {
                "artworks": ReviewArtworkSerializer(artworks, many=True, context=ctx).data,
                "artists": ReviewArtistSerializer(artists, many=True, context=ctx).data,
            }
        )


class CurationAllArtworksView(APIView):
    permission_classes = [IsAuthenticated, IsCurator]

    def get(self, request):
        qs = Artwork.objects.select_related("artist").prefetch_related("images")
        s = request.query_params.get("status")
        if s:
            qs = qs.filter(status=s)
        return Response(
            ReviewArtworkSerializer(qs, many=True, context={"request": request}).data
        )


class CurationArtworkActionView(APIView):
    permission_classes = [IsAuthenticated, IsCurator]

    def post(self, request, pk, action_name):
        artwork = get_object_or_404(Artwork, pk=pk)
        if action_name == "approve":
            artwork.approve(request.user)
        elif action_name == "reject":
            notes = (request.data.get("notes") or "").strip()
            if not notes:
                return Response(
                    {"notes": "Notes are required to reject."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            artwork.reject(request.user, notes)
        elif action_name == "feature":
            if artwork.status != ModerationStatus.PUBLISHED:
                return Response(
                    {"detail": "Only published works can be featured."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            artwork.featured = not artwork.featured
            artwork.save(update_fields=["featured", "updated_at"])
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(
            ReviewArtworkSerializer(artwork, context={"request": request}).data
        )


class CurationArtistActionView(APIView):
    permission_classes = [IsAuthenticated, IsCurator]

    def post(self, request, pk, action_name):
        artist = get_object_or_404(Artist, pk=pk)
        if action_name == "approve":
            artist.approve(request.user)
        elif action_name == "reject":
            notes = (request.data.get("notes") or "").strip()
            if not notes:
                return Response(
                    {"notes": "Notes are required to reject."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            artist.reject(request.user, notes)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(
            ReviewArtistSerializer(artist, context={"request": request}).data
        )


class CurationInquiriesView(APIView):
    permission_classes = [IsAuthenticated, IsCurator]

    def get(self, request):
        qs = Inquiry.objects.select_related("artwork", "artwork__artist")
        return Response(
            InquirySerializer(qs, many=True, context={"request": request}).data
        )


class CurationArtistsView(APIView):
    """All artist accounts (any moderation status) with their submitted work —
    the curator's people/accounts admin list. Optional ?status= filter."""

    permission_classes = [IsAuthenticated, IsCurator]

    def get(self, request):
        qs = (
            Artist.objects.select_related("user", "region")
            .prefetch_related("artworks__images")
            .order_by("-created_at")
        )
        s = request.query_params.get("status")
        if s:
            qs = qs.filter(status=s)
        return Response(
            AdminArtistSerializer(qs, many=True, context={"request": request}).data
        )


class CurationArtistPasswordView(APIView):
    """Curator sets a new password for an artist's linked auth account. Existing
    tokens are revoked so any old session must re-authenticate."""

    permission_classes = [IsAuthenticated, IsCurator]

    def post(self, request, pk):
        artist = get_object_or_404(Artist, pk=pk)
        user = artist.user
        if user is None:
            return Response(
                {"detail": "This artist has no linked account."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        password = (request.data.get("password") or "").strip()
        try:
            validate_password(password, user=user)
        except DjangoValidationError as e:
            return Response(
                {"password": list(e.messages)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.set_password(password)
        user.save(update_fields=["password"])
        Token.objects.filter(user=user).delete()
        return Response({"detail": "Password updated."})


class CurationSeoViewSet(viewsets.ModelViewSet):
    """Curator-managed SEO slots. Keyed by `key`; every editable slot is
    materialized on access so the list always shows the full set."""

    permission_classes = [IsAuthenticated, IsCurator]
    serializer_class = PageSeoSerializer
    lookup_field = "key"
    http_method_names = ["get", "put", "patch", "post"]
    pagination_class = None  # small fixed set of slots — return them all as a list

    def get_queryset(self):
        for key in EDITABLE_KEYS:
            PageSeo.objects.get_or_create(key=key)
        return PageSeo.objects.filter(key__in=EDITABLE_KEYS)

    def get_object(self):
        key = self.kwargs[self.lookup_field]
        if key not in EDITABLE_KEYS:
            from django.http import Http404

            raise Http404("Unknown SEO page.")
        obj, _ = PageSeo.objects.get_or_create(key=key)
        return obj

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=["post"], url_path="image")
    def upload_image(self, request, key=None):
        obj = self.get_object()
        f = request.FILES.get("og_image") or request.FILES.get("image")
        if not f:
            return Response(
                {"og_image": "No file provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            validate_image(f)
        except ValueError as e:
            return Response(
                {"og_image": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )
        obj.og_image = f
        obj.updated_by = request.user
        obj.save(update_fields=["og_image", "updated_by", "updated_at"])
        return Response(self.get_serializer(obj).data)

    @action(detail=True, methods=["post"], url_path="generate")
    def generate(self, request, key=None):
        """Draft a full bilingual SEO set for this slot from its description via
        OpenRouter. Returns the fields for review — does NOT save them."""
        obj = self.get_object()
        api_key = ApiKey.objects.filter(api_type=ApiType.OPENROUTER).first()
        if not api_key or not api_key.key_value:
            return Response(
                {"detail": "No OpenRouter key configured."},
                status=status.HTTP_409_CONFLICT,
            )
        # Source text: Spanish description if present, else English.
        if obj.description_es.strip():
            source_lang, description = "es", obj.description_es
        elif obj.description_en.strip():
            source_lang, description = "en", obj.description_en
        else:
            return Response(
                {"detail": "Add a description first."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        model = api_key.model or settings.OPENROUTER_MODEL or DEFAULT_MODEL
        try:
            fields = generate_seo(
                description, source_lang, api_key=api_key.key_value, model=model
            )
        except OpenRouterError as e:
            return Response({"detail": str(e)}, status=status.HTTP_502_BAD_GATEWAY)
        return Response(fields)


class CurationApiKeysView(APIView):
    """Curator-managed API keys. GET lists every supported type (with a masked
    preview + is_set flag) plus the model catalog; PUT/POST upserts a key by type."""

    permission_classes = [IsAuthenticated, IsCurator]

    def get(self, request):
        existing = {k.api_type: k for k in ApiKey.objects.all()}
        rows = []
        for value, label in ApiType.choices:
            obj = existing.get(value)
            rows.append(
                {
                    "api_type": value,
                    "label": label,
                    "is_set": bool(obj and obj.key_value),
                    "key_preview": obj.preview if obj else "",
                    "model": (obj.model if obj else "") or "",
                    "updated_at": obj.updated_at if obj else None,
                }
            )
        return Response({"keys": rows, "models": SEO_MODELS})

    def put(self, request):
        return self._upsert(request)

    def post(self, request):
        return self._upsert(request)

    def _upsert(self, request):
        api_type = (request.data.get("api_type") or "").strip()
        if api_type not in ApiType.values:
            return Response(
                {"api_type": "Unknown API type."}, status=status.HTTP_400_BAD_REQUEST
            )
        model = (request.data.get("model") or "").strip()
        if model and model not in ALLOWED_MODEL_IDS:
            return Response(
                {"model": "Unsupported model."}, status=status.HTTP_400_BAD_REQUEST
            )
        key_value = (request.data.get("key_value") or "").strip()
        existing = ApiKey.objects.filter(api_type=api_type).first()
        # The key is required on first save; on a later edit (e.g. switching the
        # model) it may be omitted to keep the stored secret.
        if not key_value and not existing:
            return Response(
                {"key_value": "This field is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        defaults = {"model": model, "updated_by": request.user}
        if key_value:
            defaults["key_value"] = key_value
        obj, _ = ApiKey.objects.update_or_create(api_type=api_type, defaults=defaults)
        return Response(
            {
                "api_type": obj.api_type,
                "is_set": bool(obj.key_value),
                "key_preview": obj.preview,
                "model": obj.model,
            }
        )


class CurationApiKeyDetailView(APIView):
    permission_classes = [IsAuthenticated, IsCurator]

    def delete(self, request, api_type):
        ApiKey.objects.filter(api_type=api_type).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

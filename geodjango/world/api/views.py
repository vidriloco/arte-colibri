"""API views: public (published-only), auth/signup, dashboard, curation."""

from django.contrib.auth import authenticate, get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from world.imaging import make_thumbnail, validate_image
from world.models import (
    Artist,
    Artwork,
    ArtworkImage,
    Inquiry,
    ModerationStatus,
    PageSeo,
    Region,
    Tag,
)
from world.models.seo import EDITABLE_KEYS
from world.seo import resolve_public

from .permissions import IsArtistOwner, IsCurator, is_curator
from .serializers import (
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
        try:
            validate_image(f)
        except ValueError as e:
            return Response({"image": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        count = artwork.images.count()
        img = ArtworkImage(artwork=artwork, position=count, is_primary=(count == 0))
        img.image = f
        img.thumbnail = make_thumbnail(f, name=f"thumb-{f.name}")
        img.save()
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

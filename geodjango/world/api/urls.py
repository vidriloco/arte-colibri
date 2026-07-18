"""URL routing for the JSON API, mounted at /api/."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"artworks", views.ArtworkViewSet, basename="artwork")
router.register(r"artists", views.ArtistViewSet, basename="artist")
router.register(
    r"dashboard/artworks", views.DashboardArtworkViewSet, basename="dash-artwork"
)
router.register(r"curation/seo", views.CurationSeoViewSet, basename="curation-seo")

urlpatterns = [
    # Public
    path("home/", views.HomeView.as_view(), name="home"),
    path("locations/", views.LocationsView.as_view(), name="locations"),
    path("meta/", views.MetaView.as_view(), name="meta"),
    path("seo/", views.PublicSeoView.as_view(), name="seo"),
    # Auth
    path("auth/signup/", views.SignupView.as_view(), name="signup"),
    path("auth/login/", views.LoginView.as_view(), name="login"),
    path("auth/logout/", views.LogoutView.as_view(), name="logout"),
    path("auth/me/", views.MeView.as_view(), name="me"),
    # Dashboard
    path("dashboard/profile/", views.DashboardProfileView.as_view(), name="dash-profile"),
    path(
        "dashboard/inquiries/",
        views.DashboardInquiriesView.as_view(),
        name="dash-inquiries",
    ),
    # Curation
    path("curation/queue/", views.CurationQueueView.as_view(), name="curation-queue"),
    path(
        "curation/artworks/",
        views.CurationAllArtworksView.as_view(),
        name="curation-artworks",
    ),
    path(
        "curation/artworks/<int:pk>/<str:action_name>/",
        views.CurationArtworkActionView.as_view(),
        name="curation-artwork-action",
    ),
    path(
        "curation/artists/<int:pk>/<str:action_name>/",
        views.CurationArtistActionView.as_view(),
        name="curation-artist-action",
    ),
    path(
        "curation/inquiries/",
        views.CurationInquiriesView.as_view(),
        name="curation-inquiries",
    ),
    path("", include(router.urls)),
]

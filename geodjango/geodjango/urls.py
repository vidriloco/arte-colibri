from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

from world.seo import AppShellView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('world.api.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # Media lives on a Docker named volume, so the host's Apache can't serve it
    # directly; Django does. Fine at this scale — object storage (S3/Spaces) is
    # the planned follow-up if traffic grows.
    urlpatterns += [
        re_path(
            r"^media/(?P<path>.*)$",
            serve,
            {"document_root": settings.MEDIA_ROOT},
        ),
    ]

# The SPA shell with server-injected SEO handles every remaining (public) route.
# This replaces the old placeholder `index` view. API / admin / media / static are
# matched above (or excluded here) so they keep their own handlers.
urlpatterns += [
    re_path(
        r"^(?!api/|admin/|media/|static/).*$",
        AppShellView.as_view(),
        name="app-shell",
    ),
]

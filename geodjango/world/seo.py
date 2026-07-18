"""Server-side SEO delivery.

Maps a request path to a page, resolves the effective SEO (curator-managed slots,
or content-derived meta for detail routes), and injects it into the SPA's HTML shell
so crawlers and link-preview scrapers see the right `<head>` on the first response.

`inject_seo`/`render_head` are pure functions (no request/DB) so they can be unit
tested against a fixture HTML string.
"""

import os
import re

from django.conf import settings
from django.http import HttpResponse
from django.utils.html import escape
from django.views import View

from world.models import Artist, Artwork, PageSeo
from world.models.seo import PageKey, RobotsDirective

# Spanish-first: the server renders the ES resolution; the SPA re-applies the head
# (and switches to EN) client-side after it hydrates.
DEFAULT_LANG = "es"

# First URL segment -> managed page key.
STATIC_ROUTES = {
    "": PageKey.HOME,
    "gallery": PageKey.GALLERY,
    "artists": PageKey.ARTISTS,
    "locations": PageKey.LOCATIONS,
}

SITE_NAME = "Arte Colibrí"


def _abs_media(request, fieldfile):
    if not fieldfile:
        return ""
    url = fieldfile.url
    return request.build_absolute_uri(url) if request is not None else url


def _lang_pick(pair, lang):
    return pair.get(lang) or pair.get("es") or pair.get("en") or ""


# ── Public (JSON) resolution — used by the client-side head manager ────────────
def resolve_public(key, request):
    """JSON-serializable resolved SEO for a managed page key."""
    if key not in PageKey.values:
        key = PageKey.DEFAULT
    r = PageSeo.resolve(key)
    return {
        "key": str(key),
        "title": r["title"],
        "description": r["description"],
        "og_title": r["og_title"],
        "og_description": r["og_description"],
        "og_image": _abs_media(request, r["og_image"]),
        "canonical": r["canonical"],
        "robots": r["robots"],
    }


# ── Server-side resolution — flat, single-language, for HTML injection ─────────
def seo_for_request(request, lang=DEFAULT_LANG):
    path = request.path.strip("/")
    segments = path.split("/") if path else [""]
    first = segments[0]

    if first == "artwork" and len(segments) >= 2:
        derived = _artwork_seo(request, segments[1], lang)
        if derived is not None:
            return derived
    elif first == "artist" and len(segments) >= 2:
        derived = _artist_seo(request, segments[1], lang)
        if derived is not None:
            return derived

    key = STATIC_ROUTES.get(first, PageKey.DEFAULT)
    return _flatten(PageSeo.resolve(key), request, lang)


def _flatten(resolved, request, lang, title=None, description=None, image=None):
    """Collapse a `PageSeo.resolve()` dict (+ optional overrides) into flat strings."""
    title = title if title is not None else _lang_pick(resolved["title"], lang)
    description = (
        description
        if description is not None
        else _lang_pick(resolved["description"], lang)
    )
    og_title = _lang_pick(resolved["og_title"], lang) or title
    og_description = _lang_pick(resolved["og_description"], lang) or description
    image = image if image is not None else _abs_media(request, resolved["og_image"])
    canonical = resolved["canonical"] or (
        request.build_absolute_uri(request.path) if request is not None else ""
    )
    return {
        "lang": lang,
        "title": title,
        "description": description,
        "og_title": og_title or title,
        "og_description": og_description or description,
        "image": image,
        "canonical": canonical,
        "robots": resolved["robots"] or RobotsDirective.INDEX.value,
        "url": request.build_absolute_uri(request.path) if request is not None else "",
    }


def _artwork_image(request, artwork):
    img = artwork.primary_image
    if not img:
        return ""
    if getattr(img, "external_url", ""):
        return img.external_url
    return _abs_media(request, img.thumbnail) or _abs_media(request, img.image)


def _artwork_seo(request, slug, lang):
    artwork = (
        Artwork.objects.public().select_related("artist").filter(slug=slug).first()
    )
    if artwork is None:
        return None
    title = getattr(artwork, f"title_{lang}", "") or artwork.title_es
    label = f"{title} · {artwork.artist.display_name} · {SITE_NAME}"
    desc = getattr(artwork, f"description_{lang}", "") or artwork.description_es
    return _flatten(
        PageSeo.resolve(PageKey.DEFAULT),
        request,
        lang,
        title=label,
        description=desc or "",
        image=_artwork_image(request, artwork),
    )


def _artist_seo(request, slug, lang):
    artist = Artist.published_objects.filter(slug=slug).first()
    if artist is None:
        return None
    label = f"{artist.display_name} · {SITE_NAME}"
    desc = getattr(artist, f"bio_{lang}", "") or artist.bio_es
    image = _abs_media(request, artist.avatar) if artist.avatar else ""
    return _flatten(
        PageSeo.resolve(PageKey.DEFAULT),
        request,
        lang,
        title=label,
        description=desc or "",
        image=image or None,
    )


# ── HTML head rendering + injection (pure) ────────────────────────────────────
def render_head(seo):
    """Build the `<head>` meta block for a flat SEO dict (values HTML-escaped)."""
    title = escape(seo.get("title") or "")
    description = escape(seo.get("description") or "")
    og_title = escape(seo.get("og_title") or seo.get("title") or "")
    og_description = escape(seo.get("og_description") or description)
    canonical = escape(seo.get("canonical") or "")
    robots = escape(seo.get("robots") or RobotsDirective.INDEX.value)
    url = escape(seo.get("url") or "")
    image = escape(seo.get("image") or "")

    tags = [
        "<title>%s</title>" % title,
        '<meta name="description" content="%s" />' % description,
        '<meta name="robots" content="%s" />' % robots,
    ]
    if canonical:
        tags.append('<link rel="canonical" href="%s" />' % canonical)
    tags += [
        '<meta property="og:type" content="website" />',
        '<meta property="og:site_name" content="%s" />' % escape(SITE_NAME),
        '<meta property="og:title" content="%s" />' % og_title,
        '<meta property="og:description" content="%s" />' % og_description,
        '<meta name="twitter:card" content="summary_large_image" />',
        '<meta name="twitter:title" content="%s" />' % og_title,
        '<meta name="twitter:description" content="%s" />' % og_description,
    ]
    if url:
        tags.append('<meta property="og:url" content="%s" />' % url)
    if image:
        tags.append('<meta property="og:image" content="%s" />' % image)
        tags.append('<meta name="twitter:image" content="%s" />' % image)
    return "\n    ".join(tags)


_TITLE_RE = re.compile(r"<title>.*?</title>", re.IGNORECASE | re.DOTALL)
_DESC_RE = re.compile(r'<meta\s+name=["\']description["\'][^>]*>', re.IGNORECASE)
_HTML_TAG_RE = re.compile(r"<html\b[^>]*>", re.IGNORECASE)


def inject_seo(html, seo):
    """Return `html` with the SPA shell's static title/description replaced by the
    server-resolved SEO head, and `<html lang>` set to the resolved language."""
    html = _TITLE_RE.sub("", html, count=1)
    html = _DESC_RE.sub("", html, count=1)
    block = "    %s\n  " % render_head(seo)
    if "</head>" in html:
        html = html.replace("</head>", block + "</head>", 1)
    else:
        html = block + html
    lang = escape(seo.get("lang") or DEFAULT_LANG)
    html = _HTML_TAG_RE.sub('<html lang="%s">' % lang, html, count=1)
    return html


# ── The app shell view ────────────────────────────────────────────────────────
_FALLBACK_SHELL = (
    "<!doctype html>\n<html lang=\"es\">\n  <head>\n"
    "    <meta charset=\"utf-8\" />\n"
    "    <title>Arte Colibrí</title>\n"
    '    <meta name="description" content="Arte Colibrí" />\n'
    "  </head>\n  <body><div id=\"root\"></div></body>\n</html>\n"
)
_shell_cache = {}


def _load_shell():
    """Read the built SPA index.html (cached outside DEBUG); fall back to a minimal
    shell when no build exists (e.g. dev, where the SPA is served by Vite instead)."""
    path = getattr(settings, "SPA_INDEX_HTML", None)
    if path and os.path.exists(path):
        if not settings.DEBUG and "html" in _shell_cache:
            return _shell_cache["html"]
        with open(path, encoding="utf-8") as fh:
            html = fh.read()
        if not settings.DEBUG:
            _shell_cache["html"] = html
        return html
    return _FALLBACK_SHELL


class AppShellView(View):
    """Serve the SPA shell with server-injected SEO for every public route."""

    def get(self, request, *args, **kwargs):
        html = inject_seo(_load_shell(), seo_for_request(request))
        return HttpResponse(html, content_type="text/html; charset=utf-8")

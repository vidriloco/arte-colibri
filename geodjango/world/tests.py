"""API tests: visibility gating, curation, ownership, inquiry, auth, bilingual."""

import json
import tempfile
from decimal import Decimal
from unittest import mock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import override_settings
from rest_framework.test import APITestCase

from world.models import Artist, Artwork, ArtworkImage, Inquiry, ModerationStatus, Region, Tag
from world.models import ApiKey, ApiType, PageSeo
from world.seo import inject_seo, render_head
from world.utils import openrouter
from world.utils.openrouter import OpenRouterError

User = get_user_model()


def make_artist(slug, published=True, with_user=True):
    user = None
    if with_user:
        user = User.objects.create_user(username=f"{slug}@x.mx", password="colibri123")
        g, _ = Group.objects.get_or_create(name=settings.ARTIST_GROUP)
        user.groups.add(g)
    return Artist.objects.create(
        slug=slug,
        display_name=slug.title(),
        user=user,
        status=ModerationStatus.PUBLISHED if published else ModerationStatus.DRAFT,
    )


def make_artwork(artist, slug, status=ModerationStatus.PUBLISHED, price="1000", featured=False, year=2024):
    return Artwork.objects.create(
        artist=artist,
        slug=slug,
        title_es=f"{slug} es",
        title_en=f"{slug} en",
        year=year,
        price=Decimal(price) if price else None,
        status=status,
        featured=featured,
    )


class VisibilityGatingTests(APITestCase):
    def setUp(self):
        self.pub_artist = make_artist("published-artist")
        self.draft_artist = make_artist("draft-artist", published=False)
        self.pub = make_artwork(self.pub_artist, "pub-work")
        self.draft = make_artwork(self.pub_artist, "draft-work", status=ModerationStatus.DRAFT)
        self.submitted = make_artwork(self.pub_artist, "sub-work", status=ModerationStatus.SUBMITTED)

    def test_gallery_lists_only_published(self):
        r = self.client.get("/api/artworks/")
        slugs = [w["slug"] for w in r.json()["results"]]
        self.assertIn("pub-work", slugs)
        self.assertNotIn("draft-work", slugs)
        self.assertNotIn("sub-work", slugs)

    def test_unpublished_detail_404(self):
        self.assertEqual(self.client.get("/api/artworks/draft-work/").status_code, 404)
        self.assertEqual(self.client.get("/api/artworks/missing/").status_code, 404)

    def test_unpublished_artist_404(self):
        self.assertEqual(
            self.client.get("/api/artists/draft-artist/").status_code, 404
        )

    def test_artist_detail_hides_unpublished_works(self):
        r = self.client.get("/api/artists/published-artist/")
        slugs = [w["slug"] for w in r.json()["works"]]
        self.assertEqual(slugs, ["pub-work"])

    def test_home_featured_before_recent(self):
        make_artwork(self.pub_artist, "feat-work", featured=True)
        r = self.client.get("/api/home/").json()
        self.assertTrue(all(w["featured"] for w in r["featured"]))


class GalleryFilterSortTests(APITestCase):
    def setUp(self):
        a = make_artist("a1")
        self.t1 = Tag.objects.create(slug="pintura", label_es="Pintura", label_en="Painting")
        self.t2 = Tag.objects.create(slug="luz", label_es="Luz", label_en="Light")
        w1 = make_artwork(a, "cheap", price="100")
        w1.tags.set([self.t1, self.t2])
        w2 = make_artwork(a, "pricey", price="900")
        w2.tags.set([self.t1])

    def test_tag_filter_and_combined(self):
        r = self.client.get("/api/artworks/?tag=pintura&tag=luz").json()
        self.assertEqual([w["slug"] for w in r["results"]], ["cheap"])

    def test_sort_price_asc(self):
        r = self.client.get("/api/artworks/?sort=price_asc").json()
        self.assertEqual([w["slug"] for w in r["results"]], ["cheap", "pricey"])

    def test_pagination_metadata(self):
        r = self.client.get("/api/artworks/").json()
        self.assertIn("count", r)
        self.assertIn("results", r)


class BilingualTests(APITestCase):
    def test_fields_are_bilingual_objects(self):
        a = make_artist("bi")
        w = make_artwork(a, "bi-work")
        r = self.client.get("/api/artworks/bi-work/").json()
        self.assertEqual(r["title"], {"es": "bi-work es", "en": "bi-work en"})
        self.assertIn("es", r["description"])
        self.assertIn("en", r["description"])


class AuthTests(APITestCase):
    def test_signup_creates_artist_in_group_with_token(self):
        r = self.client.post(
            "/api/auth/signup/",
            {"name": "Nueva Artista", "email": "nueva@x.mx", "password": "supersecret"},
            format="json",
        )
        self.assertEqual(r.status_code, 201)
        body = r.json()
        self.assertTrue(body["token"])
        self.assertEqual(body["user"]["role"], "artist")
        self.assertIsNotNone(body["user"]["artist"])
        user = User.objects.get(username="nueva@x.mx")
        self.assertTrue(user.groups.filter(name=settings.ARTIST_GROUP).exists())
        self.assertEqual(user.artist_profile.status, ModerationStatus.DRAFT)

    def test_duplicate_email_rejected(self):
        self.client.post(
            "/api/auth/signup/",
            {"name": "A", "email": "dup@x.mx", "password": "supersecret"},
            format="json",
        )
        r = self.client.post(
            "/api/auth/signup/",
            {"name": "B", "email": "dup@x.mx", "password": "supersecret"},
            format="json",
        )
        self.assertEqual(r.status_code, 400)

    def test_me_reports_role(self):
        make_artist("me-artist")
        token = self.client.post(
            "/api/auth/login/",
            {"email": "me-artist@x.mx", "password": "colibri123"},
            format="json",
        ).json()["token"]
        r = self.client.get("/api/auth/me/", HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(r.json()["role"], "artist")


class OwnershipTests(APITestCase):
    def setUp(self):
        self.a1 = make_artist("owner1")
        self.a2 = make_artist("owner2")
        self.w1 = make_artwork(self.a1, "w1", status=ModerationStatus.DRAFT)

    def _token(self, slug):
        return self.client.post(
            "/api/auth/login/",
            {"email": f"{slug}@x.mx", "password": "colibri123"},
            format="json",
        ).json()["token"]

    def test_artist_cannot_edit_others(self):
        tok = self._token("owner2")
        r = self.client.patch(
            f"/api/dashboard/artworks/{self.w1.id}/",
            {"dimensions": "hax"},
            format="json",
            HTTP_AUTHORIZATION=f"Token {tok}",
        )
        self.assertIn(r.status_code, (403, 404))

    def test_artist_cannot_self_publish(self):
        tok = self._token("owner1")
        self.client.patch(
            f"/api/dashboard/artworks/{self.w1.id}/",
            {"status": "published", "featured": True},
            format="json",
            HTTP_AUTHORIZATION=f"Token {tok}",
        )
        self.w1.refresh_from_db()
        self.assertEqual(self.w1.status, ModerationStatus.DRAFT)
        self.assertFalse(self.w1.featured)

    def test_submit_for_review(self):
        tok = self._token("owner1")
        r = self.client.post(
            f"/api/dashboard/artworks/{self.w1.id}/submit/",
            HTTP_AUTHORIZATION=f"Token {tok}",
        )
        self.assertEqual(r.json()["status"], ModerationStatus.SUBMITTED)


class CurationTests(APITestCase):
    def setUp(self):
        self.artist = make_artist("c-artist")
        self.curator = User.objects.create_user(username="cur@x.mx", password="colibri123")
        g, _ = Group.objects.get_or_create(name=settings.CURATOR_GROUP)
        self.curator.groups.add(g)
        self.w = make_artwork(self.artist, "cw", status=ModerationStatus.SUBMITTED)

    def _ctoken(self):
        return self.client.post(
            "/api/auth/login/",
            {"email": "cur@x.mx", "password": "colibri123"},
            format="json",
        ).json()["token"]

    def test_approve_publishes(self):
        tok = self._ctoken()
        r = self.client.post(
            f"/api/curation/artworks/{self.w.id}/approve/",
            HTTP_AUTHORIZATION=f"Token {tok}",
        )
        self.assertEqual(r.json()["status"], ModerationStatus.PUBLISHED)
        self.assertEqual(self.client.get("/api/artworks/cw/").status_code, 200)

    def test_reject_requires_notes(self):
        tok = self._ctoken()
        r = self.client.post(
            f"/api/curation/artworks/{self.w.id}/reject/",
            {},
            format="json",
            HTTP_AUTHORIZATION=f"Token {tok}",
        )
        self.assertEqual(r.status_code, 400)
        self.w.refresh_from_db()
        self.assertEqual(self.w.status, ModerationStatus.SUBMITTED)

    def test_reject_with_notes(self):
        tok = self._ctoken()
        self.client.post(
            f"/api/curation/artworks/{self.w.id}/reject/",
            {"notes": "Necesitamos mejores fotos."},
            format="json",
            HTTP_AUTHORIZATION=f"Token {tok}",
        )
        self.w.refresh_from_db()
        self.assertEqual(self.w.status, ModerationStatus.REJECTED)
        self.assertTrue(self.w.review_notes)
        self.assertIsNotNone(self.w.reviewed_at)

    def test_feature_requires_published(self):
        tok = self._ctoken()
        r = self.client.post(
            f"/api/curation/artworks/{self.w.id}/feature/",
            HTTP_AUTHORIZATION=f"Token {tok}",
        )
        self.assertEqual(r.status_code, 400)

    def test_non_curator_blocked(self):
        atok = self.client.post(
            "/api/auth/login/",
            {"email": "c-artist@x.mx", "password": "colibri123"},
            format="json",
        ).json()["token"]
        r = self.client.post(
            f"/api/curation/artworks/{self.w.id}/approve/",
            HTTP_AUTHORIZATION=f"Token {atok}",
        )
        self.assertEqual(r.status_code, 403)


class InquiryTests(APITestCase):
    def setUp(self):
        self.artist = make_artist("i-artist")
        self.pub = make_artwork(self.artist, "i-pub")
        self.draft = make_artwork(self.artist, "i-draft", status=ModerationStatus.DRAFT)

    def test_valid_inquiry_recorded(self):
        r = self.client.post(
            "/api/artworks/i-pub/inquiries/",
            {"name": "Ana", "email": "ana@x.mx", "message": "Hola"},
            format="json",
        )
        self.assertEqual(r.status_code, 201)
        self.assertEqual(Inquiry.objects.filter(artwork=self.pub).count(), 1)

    def test_invalid_email_rejected(self):
        r = self.client.post(
            "/api/artworks/i-pub/inquiries/",
            {"name": "Ana", "email": "nope", "message": "Hola"},
            format="json",
        )
        self.assertEqual(r.status_code, 400)
        self.assertEqual(Inquiry.objects.count(), 0)

    def test_inquiry_on_unpublished_404(self):
        r = self.client.post(
            "/api/artworks/i-draft/inquiries/",
            {"name": "Ana", "email": "ana@x.mx", "message": "Hola"},
            format="json",
        )
        self.assertEqual(r.status_code, 404)
        self.assertEqual(Inquiry.objects.count(), 0)


def _png(w=40, h=50):
    """A small, valid PNG well under every upload size limit."""
    import io
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (w, h), (180, 60, 90)).save(buf, format="PNG")
    buf.seek(0)
    buf.name = "test.png"
    return buf


def _oversized_png(min_bytes):
    """A valid PNG whose encoded size exceeds `min_bytes` (random noise resists
    compression, so a modest canvas already blows past the KB limits)."""
    import io
    import os
    from PIL import Image
    for side in (500, 800, 1200, 1800):
        buf = io.BytesIO()
        Image.frombytes("RGB", (side, side), os.urandom(side * side * 3)).save(
            buf, format="PNG"
        )
        if buf.tell() > min_bytes:
            break
    buf.seek(0)
    buf.name = "big.png"
    return buf


class _S3MockMixin:
    """Replace the boto3 client with a MagicMock so uploads/deletes never hit a
    live bucket; key derivation and public-URL construction still run for real."""

    def setUp(self):
        super().setUp()
        from unittest import mock
        self.s3_client = mock.MagicMock()
        patcher = mock.patch(
            "world.utils.s3._get_s3_client", return_value=self.s3_client
        )
        self.addCleanup(patcher.stop)
        patcher.start()


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class ImageTests(_S3MockMixin, APITestCase):
    def setUp(self):
        super().setUp()
        self.artist = make_artist("img-artist")
        self.w = make_artwork(self.artist, "img-w", status=ModerationStatus.DRAFT)

    def _tok(self, email="img-artist@x.mx"):
        return self.client.post(
            "/api/auth/login/",
            {"email": email, "password": "colibri123"},
            format="json",
        ).json()["token"]

    def _upload(self, f, tok=None):
        tok = tok or self._tok()
        return self.client.post(
            f"/api/dashboard/artworks/{self.w.id}/images/",
            {"image": f},
            format="multipart",
            HTTP_AUTHORIZATION=f"Token {tok}",
        )

    def test_first_image_is_primary_and_stored_on_s3(self):
        r = self._upload(_png())
        self.assertEqual(r.status_code, 201)
        self.assertTrue(r.json()["is_primary"])
        # Original + thumbnail both pushed to S3 and their URLs persisted.
        self.assertEqual(self.s3_client.put_object.call_count, 2)
        img = ArtworkImage.objects.get()
        self.assertIn("arte-colibri.s3", img.external_url)
        self.assertTrue(img.thumbnail_url.endswith(".jpg"))
        self.assertEqual(r.json()["url"], img.external_url)

    def test_non_image_rejected(self):
        import io
        bad = io.BytesIO(b"not an image")
        bad.name = "bad.png"
        r = self._upload(bad)
        self.assertEqual(r.status_code, 400)
        self.assertEqual(ArtworkImage.objects.count(), 0)
        self.s3_client.put_object.assert_not_called()

    def test_image_within_limit_accepted(self):
        r = self._upload(_png())
        self.assertEqual(r.status_code, 201)

    def test_oversized_image_rejected(self):
        r = self._upload(_oversized_png(500 * 1024))
        self.assertEqual(r.status_code, 400)
        self.assertIn("500 KB", r.json()["image"])
        self.assertEqual(ArtworkImage.objects.count(), 0)
        self.s3_client.put_object.assert_not_called()

    def test_non_owner_cannot_upload(self):
        make_artist("intruder")
        r = self._upload(_png(), tok=self._tok("intruder@x.mx"))
        self.assertIn(r.status_code, (403, 404))
        self.s3_client.put_object.assert_not_called()

    def test_anonymous_cannot_upload(self):
        r = self.client.post(
            f"/api/dashboard/artworks/{self.w.id}/images/",
            {"image": _png()},
            format="multipart",
        )
        self.assertEqual(r.status_code, 401)

    def test_delete_removes_s3_objects_and_reassigns_primary(self):
        tok = self._tok()
        first = self._upload(_png(), tok=tok).json()
        self._upload(_png(), tok=tok)
        self.s3_client.reset_mock()
        r = self.client.delete(
            f"/api/dashboard/artworks/{self.w.id}/images/{first['id']}/",
            HTTP_AUTHORIZATION=f"Token {tok}",
        )
        self.assertEqual(r.status_code, 204)
        # Both S3 objects (original + thumb) deleted; next image becomes primary.
        self.assertEqual(self.s3_client.delete_object.call_count, 2)
        self.assertTrue(ArtworkImage.objects.get().is_primary)

    def test_delete_tolerates_missing_s3_object(self):
        tok = self._tok()
        img = self._upload(_png(), tok=tok).json()
        self.s3_client.delete_object.side_effect = Exception("already gone")
        r = self.client.delete(
            f"/api/dashboard/artworks/{self.w.id}/images/{img['id']}/",
            HTTP_AUTHORIZATION=f"Token {tok}",
        )
        self.assertEqual(r.status_code, 204)
        self.assertEqual(ArtworkImage.objects.count(), 0)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class AvatarTests(_S3MockMixin, APITestCase):
    def setUp(self):
        super().setUp()
        self.artist = make_artist("ava-artist")

    def _tok(self, email="ava-artist@x.mx"):
        return self.client.post(
            "/api/auth/login/",
            {"email": email, "password": "colibri123"},
            format="json",
        ).json()["token"]

    def _upload(self, f, tok=None):
        tok = tok or self._tok()
        return self.client.post(
            "/api/dashboard/profile/avatar/",
            {"avatar": f},
            format="multipart",
            HTTP_AUTHORIZATION=f"Token {tok}",
        )

    def test_avatar_within_limit_stored_on_s3(self):
        r = self._upload(_png())
        self.assertEqual(r.status_code, 200)
        self.s3_client.put_object.assert_called_once()
        self.artist.refresh_from_db()
        self.assertIn("artists/avatars/", self.s3_client.put_object.call_args.kwargs["Key"])
        self.assertIn("arte-colibri.s3", self.artist.avatar_url)
        self.assertEqual(r.json()["avatar"], self.artist.avatar_url)

    def test_oversized_avatar_rejected(self):
        r = self._upload(_oversized_png(200 * 1024))
        self.assertEqual(r.status_code, 400)
        self.assertIn("200 KB", r.json()["avatar"])
        self.s3_client.put_object.assert_not_called()
        self.artist.refresh_from_db()
        self.assertEqual(self.artist.avatar_url, "")

    def test_non_image_avatar_rejected(self):
        import io
        bad = io.BytesIO(b"nope")
        bad.name = "bad.png"
        r = self._upload(bad)
        self.assertEqual(r.status_code, 400)
        self.s3_client.put_object.assert_not_called()

    def test_anonymous_cannot_set_avatar(self):
        r = self.client.post(
            "/api/dashboard/profile/avatar/", {"avatar": _png()}, format="multipart"
        )
        self.assertEqual(r.status_code, 401)


@override_settings(
    MEDIA_ROOT=tempfile.mkdtemp(),
    AWS_ACCESS_KEY_ID=None,
    AWS_SECRET_ACCESS_KEY=None,
)
class S3UnconfiguredTests(APITestCase):
    """With no AWS credentials the upload fails loudly instead of silently
    writing to local disk."""

    def setUp(self):
        self.artist = make_artist("noaws-artist")
        self.w = make_artwork(self.artist, "noaws-w", status=ModerationStatus.DRAFT)

    def _tok(self):
        return self.client.post(
            "/api/auth/login/",
            {"email": "noaws-artist@x.mx", "password": "colibri123"},
            format="json",
        ).json()["token"]

    def test_upload_without_credentials_errors_and_writes_nothing(self):
        self.client.raise_request_exception = False
        r = self.client.post(
            f"/api/dashboard/artworks/{self.w.id}/images/",
            {"image": _png()},
            format="multipart",
            HTTP_AUTHORIZATION=f"Token {self._tok()}",
        )
        self.assertEqual(r.status_code, 500)
        # The just-created row is rolled back; no image persists.
        self.assertEqual(ArtworkImage.objects.count(), 0)


class SeoResolutionTests(APITestCase):
    def test_public_resolve_bilingual_shape(self):
        r = self.client.get("/api/seo/?page=home").json()
        for field in ("title", "description", "og_title", "og_description"):
            self.assertIn("es", r[field])
            self.assertIn("en", r[field])
        self.assertEqual(r["robots"], "index,follow")

    def test_page_field_falls_back_to_default_slot(self):
        PageSeo.objects.create(key="default", description_es="Default desc")
        PageSeo.objects.create(key="artists", title_es="Artistas")
        r = self.client.get("/api/seo/?page=artists").json()
        self.assertEqual(r["title"]["es"], "Artistas")
        # description was blank on the artists row -> inherits the default slot
        self.assertEqual(r["description"]["es"], "Default desc")

    def test_og_falls_back_to_title(self):
        PageSeo.objects.create(key="gallery", title_es="Galería", title_en="Gallery")
        r = self.client.get("/api/seo/?page=gallery").json()
        self.assertEqual(r["og_title"]["es"], "Galería")

    def test_unknown_page_uses_default(self):
        r = self.client.get("/api/seo/?page=bogus")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["key"], "default")

    def test_resolve_includes_image_alt_and_keywords(self):
        PageSeo.objects.create(
            key="home",
            image_alt_es="Colección Arte Colibrí",
            keywords_es="arte, galería, CDMX",
        )
        r = self.client.get("/api/seo/?page=home").json()
        for field in ("image_alt", "keywords"):
            self.assertIn("es", r[field])
            self.assertIn("en", r[field])
        self.assertEqual(r["image_alt"]["es"], "Colección Arte Colibrí")
        self.assertEqual(r["keywords"]["es"], "arte, galería, CDMX")


class SeoPermissionTests(APITestCase):
    def setUp(self):
        self.curator = User.objects.create_user(username="cur@x.mx", password="colibri123")
        g, _ = Group.objects.get_or_create(name=settings.CURATOR_GROUP)
        self.curator.groups.add(g)
        make_artist("plain-artist")  # artist user for the negative case

    def _ctoken(self):
        return self.client.post(
            "/api/auth/login/",
            {"email": "cur@x.mx", "password": "colibri123"},
            format="json",
        ).json()["token"]

    def test_anonymous_cannot_read_curation_seo(self):
        self.assertIn(self.client.get("/api/curation/seo/").status_code, (401, 403))

    def test_artist_cannot_write_seo(self):
        tok = self.client.post(
            "/api/auth/login/",
            {"email": "plain-artist@x.mx", "password": "colibri123"},
            format="json",
        ).json()["token"]
        r = self.client.patch(
            "/api/curation/seo/home/",
            {"title": {"es": "hax", "en": "hax"}},
            format="json",
            HTTP_AUTHORIZATION=f"Token {tok}",
        )
        self.assertEqual(r.status_code, 403)

    def test_curator_lists_all_editable_slots(self):
        tok = self._ctoken()
        r = self.client.get(
            "/api/curation/seo/", HTTP_AUTHORIZATION=f"Token {tok}"
        ).json()
        keys = {row["key"] for row in r}
        self.assertEqual(keys, {"default", "home", "gallery", "artists", "locations"})

    def test_curator_updates_slot(self):
        tok = self._ctoken()
        r = self.client.patch(
            "/api/curation/seo/gallery/",
            {"title": {"es": "Galería curada", "en": "Curated gallery"}, "robots": "noindex,follow"},
            format="json",
            HTTP_AUTHORIZATION=f"Token {tok}",
        )
        self.assertEqual(r.status_code, 200)
        pub = self.client.get("/api/seo/?page=gallery").json()
        self.assertEqual(pub["title"]["es"], "Galería curada")
        self.assertEqual(pub["robots"], "noindex,follow")

    def test_curator_saves_image_alt_and_keywords(self):
        tok = self._ctoken()
        r = self.client.patch(
            "/api/curation/seo/home/",
            {
                "image_alt": {"es": "Portada", "en": "Cover"},
                "keywords": {"es": "arte, galería", "en": "art, gallery"},
            },
            format="json",
            HTTP_AUTHORIZATION=f"Token {tok}",
        )
        self.assertEqual(r.status_code, 200)
        pub = self.client.get("/api/seo/?page=home").json()
        self.assertEqual(pub["image_alt"]["en"], "Cover")
        self.assertEqual(pub["keywords"]["es"], "arte, galería")


class SeoInjectionTests(APITestCase):
    SHELL = (
        "<!doctype html>\n<html lang=\"en\">\n<head>\n"
        "<title>Old</title>\n"
        '<meta name="description" content="old" />\n'
        "</head>\n<body><div id=\"root\"></div></body>\n</html>"
    )

    def test_render_head_contains_core_tags(self):
        head = render_head(
            {
                "title": "T & Co",
                "description": "D",
                "robots": "noindex,follow",
                "canonical": "https://x/y",
                "image": "https://x/i.jpg",
                "image_alt": "A photo",
                "keywords": "art, gallery",
                "url": "https://x/y",
            }
        )
        self.assertIn("<title>T &amp; Co</title>", head)  # escaped
        self.assertIn('name="robots" content="noindex,follow"', head)
        self.assertIn('rel="canonical" href="https://x/y"', head)
        self.assertIn('property="og:image" content="https://x/i.jpg"', head)
        self.assertIn('name="keywords" content="art, gallery"', head)
        self.assertIn('property="og:image:alt" content="A photo"', head)
        self.assertIn('name="twitter:image:alt" content="A photo"', head)

    def test_render_head_omits_empty_optional_tags(self):
        head = render_head({"title": "T", "description": "D"})
        self.assertNotIn('name="keywords"', head)  # no keywords → tag omitted
        self.assertNotIn("og:image:alt", head)  # no image → no alt

    def test_inject_replaces_title_and_lang(self):
        out = inject_seo(self.SHELL, {"title": "New", "description": "N", "lang": "es"})
        self.assertIn("<title>New</title>", out)
        self.assertNotIn("<title>Old</title>", out)
        self.assertNotIn('content="old"', out)
        self.assertIn('<html lang="es">', out)

    def test_shell_route_injects_managed_title(self):
        PageSeo.objects.create(key="gallery", title_es="Galería SSR", robots="noindex,follow")
        html = self.client.get("/gallery").content.decode()
        self.assertIn("<title>Galería SSR</title>", html)
        self.assertIn('name="robots" content="noindex,follow"', html)

    def test_detail_route_derives_from_artwork(self):
        artist = make_artist("ssr-artist")
        make_artwork(artist, "ssr-work")
        html = self.client.get("/artwork/ssr-work/").content.decode()
        self.assertIn("ssr-work es", html)  # artwork title_es appears in <title>
        self.assertIn("Ssr-Artist", html)


class ArtworkFormFieldsTests(APITestCase):
    def setUp(self):
        self.artist = make_artist("form-artist")

    def _tok(self):
        return self.client.post(
            "/api/auth/login/", {"email": "form-artist@x.mx", "password": "colibri123"}, format="json"
        ).json()["token"]

    def test_english_optional_not_cross_filled_and_sold_price(self):
        r = self.client.post(
            "/api/dashboard/artworks/",
            {
                "title": {"es": "Obra", "en": ""},
                "description": {"es": "Una descripción", "en": ""},
                "medium": {"es": "Óleo", "en": ""},
                "dimensions": "60x80",
                "year": 2025,
                "price": "1000",
                "availability": "sold",
                "sold_price": "1500",
                "tags": [],
            },
            format="json", HTTP_AUTHORIZATION=f"Token {self._tok()}",
        )
        self.assertEqual(r.status_code, 201, r.content)
        art = Artwork.objects.get(slug=r.json()["slug"])
        self.assertEqual(art.title_es, "Obra")
        self.assertEqual(art.title_en, "")           # English left blank (no cross-fill)
        self.assertEqual(art.description_en, "")      # blank, not duplicated from Spanish
        self.assertEqual(art.availability, "sold")
        self.assertEqual(str(art.sold_price), "1500.00")
        # Read-back exposes English as empty string (display falls back client-side).
        self.assertEqual(r.json()["title"]["en"], "")
        self.assertEqual(r.json()["sold_price"], "1500.00")


def _curator(email="curk@x.mx"):
    user = User.objects.create_user(username=email, password="colibri123")
    g, _ = Group.objects.get_or_create(name=settings.CURATOR_GROUP)
    user.groups.add(g)
    return user


class ApiKeysTests(APITestCase):
    def setUp(self):
        _curator()
        make_artist("plain-artist-k")  # for the non-curator case

    def _ctok(self):
        return self.client.post(
            "/api/auth/login/", {"email": "curk@x.mx", "password": "colibri123"}, format="json"
        ).json()["token"]

    def test_upsert_masks_secret_and_lists_models(self):
        tok = self._ctok()
        r = self.client.put(
            "/api/curation/api-keys/",
            {"api_type": "openrouter", "key_value": "sk-secret-abcd", "model": "openai/gpt-4o-mini"},
            format="json", HTTP_AUTHORIZATION=f"Token {tok}",
        )
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["is_set"])
        self.assertNotIn("sk-secret-abcd", json.dumps(r.json()))  # never echoed
        lst = self.client.get("/api/curation/api-keys/", HTTP_AUTHORIZATION=f"Token {tok}").json()
        row = next(k for k in lst["keys"] if k["api_type"] == "openrouter")
        self.assertTrue(row["is_set"])
        self.assertEqual(row["key_preview"], "…abcd")
        self.assertEqual(row["model"], "openai/gpt-4o-mini")
        self.assertNotIn("sk-secret-abcd", json.dumps(lst))  # secret never in list
        self.assertEqual(len(lst["models"]), 4)  # price/power-equivalent model options

    def test_model_only_update_keeps_key(self):
        tok = self._ctok()
        self.client.put(
            "/api/curation/api-keys/", {"api_type": "openrouter", "key_value": "sk-first-1111"},
            format="json", HTTP_AUTHORIZATION=f"Token {tok}",
        )
        r = self.client.put(
            "/api/curation/api-keys/", {"api_type": "openrouter", "model": "google/gemini-2.0-flash-001"},
            format="json", HTTP_AUTHORIZATION=f"Token {tok}",
        )
        self.assertEqual(r.status_code, 200)
        k = ApiKey.objects.get(api_type="openrouter")
        self.assertEqual(k.key_value, "sk-first-1111")  # secret preserved
        self.assertEqual(k.model, "google/gemini-2.0-flash-001")

    def test_invalid_model_rejected(self):
        tok = self._ctok()
        r = self.client.put(
            "/api/curation/api-keys/", {"api_type": "openrouter", "key_value": "x", "model": "evil/pricey"},
            format="json", HTTP_AUTHORIZATION=f"Token {tok}",
        )
        self.assertEqual(r.status_code, 400)

    def test_delete(self):
        tok = self._ctok()
        self.client.put(
            "/api/curation/api-keys/", {"api_type": "openrouter", "key_value": "sk-x-1234"},
            format="json", HTTP_AUTHORIZATION=f"Token {tok}",
        )
        r = self.client.delete("/api/curation/api-keys/openrouter/", HTTP_AUTHORIZATION=f"Token {tok}")
        self.assertEqual(r.status_code, 204)
        self.assertFalse(ApiKey.objects.filter(api_type="openrouter").exists())

    def test_non_curator_and_anon_blocked(self):
        self.assertIn(self.client.get("/api/curation/api-keys/").status_code, (401, 403))
        atok = self.client.post(
            "/api/auth/login/", {"email": "plain-artist-k@x.mx", "password": "colibri123"}, format="json"
        ).json()["token"]
        r = self.client.put(
            "/api/curation/api-keys/", {"api_type": "openrouter", "key_value": "x"},
            format="json", HTTP_AUTHORIZATION=f"Token {atok}",
        )
        self.assertIn(r.status_code, (401, 403))


class SeoGenerateTests(APITestCase):
    def setUp(self):
        _curator()

    def _ctok(self):
        return self.client.post(
            "/api/auth/login/", {"email": "curk@x.mx", "password": "colibri123"}, format="json"
        ).json()["token"]

    def _key(self, model=""):
        ApiKey.objects.create(api_type=ApiType.OPENROUTER, key_value="sk-test-1234", model=model)

    def test_generate_returns_bilingual_and_saves_nothing(self):
        self._key()
        PageSeo.objects.create(key="home", description_es="Una galería de arte curado.")
        fields = ["title", "description", "og_title", "og_description", "keywords", "image_alt"]
        fake = {f: {"es": f + "_es", "en": f + "_en"} for f in fields}
        with mock.patch("world.api.views.generate_seo", return_value=fake) as m:
            r = self.client.post(
                "/api/curation/seo/home/generate/", {}, format="json",
                HTTP_AUTHORIZATION=f"Token {self._ctok()}",
            )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["title"]["es"], "title_es")
        self.assertEqual(m.call_args[0][1], "es")  # Spanish is the source
        self.assertEqual(PageSeo.objects.get(key="home").title_es, "")  # nothing saved

    def test_generate_uses_english_when_no_spanish(self):
        self._key()
        PageSeo.objects.create(key="home", description_en="A curated gallery.")
        with mock.patch("world.api.views.generate_seo", return_value={}) as m:
            self.client.post(
                "/api/curation/seo/home/generate/", {}, format="json",
                HTTP_AUTHORIZATION=f"Token {self._ctok()}",
            )
        self.assertEqual(m.call_args[0][1], "en")

    def test_generate_409_without_key(self):
        PageSeo.objects.create(key="home", description_es="x")
        r = self.client.post(
            "/api/curation/seo/home/generate/", {}, format="json",
            HTTP_AUTHORIZATION=f"Token {self._ctok()}",
        )
        self.assertEqual(r.status_code, 409)

    def test_generate_400_without_description(self):
        self._key()  # home slot auto-materializes blank
        r = self.client.post(
            "/api/curation/seo/home/generate/", {}, format="json",
            HTTP_AUTHORIZATION=f"Token {self._ctok()}",
        )
        self.assertEqual(r.status_code, 400)

    def test_generate_provider_error_leaves_slot_untouched(self):
        self._key()
        PageSeo.objects.create(key="home", description_es="x", title_es="")
        with mock.patch("world.api.views.generate_seo", side_effect=OpenRouterError("boom")):
            r = self.client.post(
                "/api/curation/seo/home/generate/", {}, format="json",
                HTTP_AUTHORIZATION=f"Token {self._ctok()}",
            )
        self.assertEqual(r.status_code, 502)
        self.assertEqual(PageSeo.objects.get(key="home").title_es, "")


class OpenRouterClientTests(APITestCase):
    def test_parses_valid_json_and_normalizes_missing_fields(self):
        resp = mock.Mock(status_code=200)
        resp.json.return_value = {
            "choices": [{"message": {"content": json.dumps({"title": {"es": "T", "en": "Te"}})}}]
        }
        with mock.patch("world.utils.openrouter.requests.post", return_value=resp):
            out = openrouter.generate_seo("desc", "es", api_key="k", model="openai/gpt-4o-mini")
        self.assertEqual(out["title"], {"es": "T", "en": "Te"})
        self.assertEqual(out["keywords"], {"es": "", "en": ""})  # missing field filled in

    def test_bad_json_raises(self):
        resp = mock.Mock(status_code=200)
        resp.json.return_value = {"choices": [{"message": {"content": "not json"}}]}
        with mock.patch("world.utils.openrouter.requests.post", return_value=resp):
            with self.assertRaises(OpenRouterError):
                openrouter.generate_seo("d", "es", api_key="k")

    def test_http_error_raises(self):
        resp = mock.Mock(status_code=402, text="no credits")
        with mock.patch("world.utils.openrouter.requests.post", return_value=resp):
            with self.assertRaises(OpenRouterError):
                openrouter.generate_seo("d", "es", api_key="k")

    def test_unknown_model_falls_back_to_default(self):
        self.assertEqual(openrouter.resolve_model("evil/pricey"), openrouter.DEFAULT_MODEL)
        self.assertEqual(openrouter.resolve_model("openai/gpt-4o-mini"), "openai/gpt-4o-mini")

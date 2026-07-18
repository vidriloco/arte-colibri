"""API tests: visibility gating, curation, ownership, inquiry, auth, bilingual."""

import tempfile
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import override_settings
from rest_framework.test import APITestCase

from world.models import Artist, Artwork, ArtworkImage, Inquiry, ModerationStatus, Region, Tag
from world.models import PageSeo
from world.seo import inject_seo, render_head

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


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class ImageTests(APITestCase):
    def setUp(self):
        self.artist = make_artist("img-artist")
        self.w = make_artwork(self.artist, "img-w", status=ModerationStatus.DRAFT)

    def _tok(self):
        return self.client.post(
            "/api/auth/login/",
            {"email": "img-artist@x.mx", "password": "colibri123"},
            format="json",
        ).json()["token"]

    def _png(self):
        import io
        from PIL import Image
        buf = io.BytesIO()
        Image.new("RGB", (40, 50), (180, 60, 90)).save(buf, format="PNG")
        buf.seek(0)
        buf.name = "test.png"
        return buf

    def test_first_image_is_primary(self):
        tok = self._tok()
        r = self.client.post(
            f"/api/dashboard/artworks/{self.w.id}/images/",
            {"image": self._png()},
            format="multipart",
            HTTP_AUTHORIZATION=f"Token {tok}",
        )
        self.assertEqual(r.status_code, 201)
        self.assertTrue(r.json()["is_primary"])

    def test_non_image_rejected(self):
        import io
        tok = self._tok()
        bad = io.BytesIO(b"not an image")
        bad.name = "bad.png"
        r = self.client.post(
            f"/api/dashboard/artworks/{self.w.id}/images/",
            {"image": bad},
            format="multipart",
            HTTP_AUTHORIZATION=f"Token {tok}",
        )
        self.assertEqual(r.status_code, 400)
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
                "url": "https://x/y",
            }
        )
        self.assertIn("<title>T &amp; Co</title>", head)  # escaped
        self.assertIn('name="robots" content="noindex,follow"', head)
        self.assertIn('rel="canonical" href="https://x/y"', head)
        self.assertIn('property="og:image" content="https://x/i.jpg"', head)

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

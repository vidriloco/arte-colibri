"""Seed Arte Colibrí with the prototype's artists, artworks, regions and tags.

Creates the Artist/Curator groups, a demo curator, and one demo artist login.
Idempotent: safe to re-run. Images reference Unsplash URLs (external_url) so the
seed is faithful to the design without bundling binaries.

    python manage.py seed_demo
"""

import re
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction

from world.models import (
    Artist,
    Artwork,
    ArtworkImage,
    ModerationStatus,
    PageSeo,
    Region,
    Tag,
)


def _parse_dims(s):
    """Parse a legacy `"W × H [× D] cm"` string into width/height/depth numbers."""
    nums = [Decimal(n) for n in re.findall(r"[\d.]+", s or "")][:3]
    keys = ["width", "height", "depth"]
    return {keys[i]: nums[i] for i in range(len(nums))}

User = get_user_model()


def uns(photo_id, w=1100):
    return f"https://images.unsplash.com/photo-{photo_id}?w={w}&q=80&auto=format&fit=crop"


REGIONS = [
    ("roma-condesa", "Roma · Condesa", "Roma · Condesa", 0),
    ("coyoacan", "Coyoacán", "Coyoacán", 1),
    ("san-angel", "San Ángel", "San Ángel", 2),
    ("centro", "Centro · Doctores", "Centro · Doctores", 3),
    ("tlalpan", "Tlalpan", "Tlalpan", 4),
    ("polanco", "Polanco", "Polanco", 5),
]

TAGS = [
    ("pintura", "Pintura", "Painting"),
    ("escultura", "Escultura", "Sculpture"),
    ("fotografia", "Fotografía", "Photography"),
    ("ceramica", "Cerámica", "Ceramics"),
    ("textil", "Textil", "Textile"),
    ("grabado", "Grabado", "Printmaking"),
    ("abstracto", "Abstracto", "Abstract"),
    ("luz", "Luz", "Light"),
    ("piedra", "Piedra", "Stone"),
    ("documental", "Documental", "Documentary"),
    ("objeto", "Objeto", "Object"),
    ("tinte-natural", "Tinte natural", "Natural dye"),
    ("obra-sobre-papel", "Obra sobre papel", "Works on paper"),
]

ARTISTS = [
    {
        "slug": "mariana-quiroz", "name": "Mariana Quiroz Salgado",
        "city": "Coyoacán", "region": "coyoacan",
        "discipline_es": "Pintura", "discipline_en": "Painting", "since": 2022,
        "bio_es": "Pintora egresada de la ENPEG \"La Esmeralda\". Su práctica explora la luz tamizada de los patios coloniales del sur de la ciudad. Trabaja con óleo sobre lino preparado a mano.",
        "bio_en": "Painter trained at ENPEG \"La Esmeralda\". Her practice explores the filtered light of colonial courtyards in the south of the city. She works in oil on hand-prepared linen.",
        "web": "marianaquiroz.studio", "instagram": "@mariana.quiroz",
    },
    {
        "slug": "ernesto-vela", "name": "Ernesto Vela Bautista",
        "city": "Roma Norte", "region": "roma-condesa",
        "discipline_es": "Escultura", "discipline_en": "Sculpture", "since": 2021,
        "bio_es": "Escultor que talla en cantera y mármol travertino de Tepeaca. Sus formas dialogan con la arquitectura prehispánica y la geometría modernista.",
        "bio_en": "Sculptor working in cantera stone and Tepeaca travertine. His forms converse with pre-Hispanic architecture and modernist geometry.",
        "web": "vela-estudio.mx", "instagram": "@vela.estudio",
    },
    {
        "slug": "sofia-marin", "name": "Sofía Marín Lara",
        "city": "San Ángel", "region": "san-angel",
        "discipline_es": "Fotografía", "discipline_en": "Photography", "since": 2023,
        "bio_es": "Fotógrafa documental. Trabaja con película de medio formato, retratando los oficios y mercados del centro y sur de la ciudad.",
        "bio_en": "Documentary photographer. She works in medium-format film, portraying the trades and markets of the city's center and south.",
        "web": "sofiamarin.foto", "instagram": "@sofia.lara.foto",
    },
    {
        "slug": "diego-resendiz", "name": "Diego Reséndiz Coria",
        "city": "Doctores", "region": "centro",
        "discipline_es": "Cerámica", "discipline_en": "Ceramics", "since": 2020,
        "bio_es": "Ceramista. Su obra parte del barro negro de Oaxaca y la vidriado de plomo libre. Mantiene un taller compartido en la colonia Doctores.",
        "bio_en": "Ceramist. His work begins with Oaxacan black clay and lead-free glazes. He keeps a shared studio in the Doctores neighborhood.",
        "web": "barro-resendiz.mx", "instagram": "@barro.resendiz",
    },
    {
        "slug": "luciana-pacheco", "name": "Luciana Pacheco Riva",
        "city": "Condesa", "region": "roma-condesa",
        "discipline_es": "Textil", "discipline_en": "Textile", "since": 2022,
        "bio_es": "Artista textil. Teje en telar de cintura usando algodón y lana teñidos con grana cochinilla, añil y palo de Brasil.",
        "bio_en": "Textile artist. She weaves on a backstrap loom with cotton and wool dyed in cochineal, indigo, and brazilwood.",
        "web": "pacheco-textil.mx", "instagram": "@luciana.textil",
    },
    {
        "slug": "tomas-iturbide", "name": "Tomás Iturbide Caro",
        "city": "Tlalpan", "region": "tlalpan",
        "discipline_es": "Grabado", "discipline_en": "Printmaking", "since": 2021,
        "bio_es": "Grabador. Trabaja la xilografía y la litografía en piedra. Sus ediciones se imprimen en su taller cerca del bosque de Tlalpan.",
        "bio_en": "Printmaker. He works in woodcut and stone lithography. His editions are printed at his studio near the Tlalpan forest.",
        "web": "iturbide-grabado.mx", "instagram": "@iturbide.grabado",
    },
]

ARTWORKS = [
    {
        "slug": "patio-sur-iii", "artist": "mariana-quiroz",
        "title_es": "Patio sur III", "title_en": "South Courtyard III",
        "year": 2024, "medium_es": "Óleo sobre lino", "medium_en": "Oil on linen",
        "dimensions": "120 × 90 cm", "price": "48000", "availability": "available",
        "featured": True, "tags": ["pintura", "abstracto", "luz"],
        "images": ["1547826039-bfc35e0f1ea8", "1578926375605-eaf7559b1458", "1579783901586-d88db74b4fe4"],
        "description_es": "Tercera entrega de la serie iniciada en 2023, donde la artista descompone la luz de un patio en Coyoacán al filo de las cinco de la tarde.",
        "description_en": "Third entry in the series begun in 2023, in which the artist decomposes the light of a Coyoacán courtyard at five in the afternoon.",
    },
    {
        "slug": "cantera-fragmento-ii", "artist": "ernesto-vela",
        "title_es": "Cantera, fragmento II", "title_en": "Cantera, Fragment II",
        "year": 2024, "medium_es": "Cantera rosa tallada", "medium_en": "Carved pink cantera",
        "dimensions": "42 × 28 × 22 cm", "price": None, "availability": "available",
        "featured": True, "tags": ["escultura", "piedra"],
        "images": ["1605000797499-95a51c5269ae", "1578321272176-b7bbc0679853", "1610701596007-11502861dcfa"],
        "description_es": "Pieza tallada en cantera rosa de Tezontepec. Estudia la transición entre la superficie pulida y el corte bruto.",
        "description_en": "Piece carved in pink Tezontepec cantera. It studies the transition between polished surface and raw cut.",
    },
    {
        "slug": "merced-jueves", "artist": "sofia-marin",
        "title_es": "La Merced, jueves", "title_en": "La Merced, Thursday",
        "year": 2025, "medium_es": "Fotografía analógica, impresión en gelatina de plata",
        "medium_en": "Analog photograph, silver gelatin print",
        "dimensions": "50 × 40 cm", "price": "14500", "availability": "available",
        "featured": False, "tags": ["fotografia", "documental"],
        "images": ["1551892374-ecf8754cf8b0", "1521714161819-15534968fc5f"],
        "description_es": "Edición de 7 + 2 PA. Impresión sobre papel baritado, montada en passe-partout neutro.",
        "description_en": "Edition of 7 + 2 AP. Printed on baryta paper, mounted in a neutral passe-partout.",
    },
    {
        "slug": "barro-negro-vasija", "artist": "diego-resendiz",
        "title_es": "Vasija, barro negro", "title_en": "Vessel, Black Clay",
        "year": 2024, "medium_es": "Barro negro de Oaxaca", "medium_en": "Oaxacan black clay",
        "dimensions": "34 × 24 × 24 cm", "price": "9800", "availability": "sold",
        "featured": False, "tags": ["ceramica", "objeto"],
        "images": ["1610701596007-11502861dcfa", "1578321272176-b7bbc0679853"],
        "description_es": "Pieza torneada y bruñida a mano. Acabado mate sin esmaltar.",
        "description_en": "Hand-thrown and burnished piece. Matte, unglazed finish.",
    },
    {
        "slug": "telar-grana", "artist": "luciana-pacheco",
        "title_es": "Telar, grana", "title_en": "Loom, Cochineal",
        "year": 2025, "medium_es": "Lana teñida con grana cochinilla sobre algodón",
        "medium_en": "Cochineal-dyed wool on cotton",
        "dimensions": "180 × 120 cm", "price": "32000", "availability": "available",
        "featured": True, "tags": ["textil", "tinte-natural"],
        "images": ["1549887534-1541e9326642", "1577083552431-6e5fd01988a5", "1556139943-4bdca53adf1e"],
        "description_es": "Pieza tejida en telar de cintura durante cuatro meses. El rojo proviene de cochinilla cultivada en Oaxaca.",
        "description_en": "Woven on a backstrap loom over four months. The red comes from cochineal cultivated in Oaxaca.",
    },
    {
        "slug": "xilografia-pirul", "artist": "tomas-iturbide",
        "title_es": "Pirul, xilografía", "title_en": "Pirul, Woodcut",
        "year": 2024, "medium_es": "Xilografía sobre papel japonés", "medium_en": "Woodcut on Japanese paper",
        "dimensions": "70 × 50 cm", "price": "6500", "availability": "available",
        "featured": False, "tags": ["grabado", "obra-sobre-papel"],
        "images": ["1579783902614-a3fb3927b6a5", "1582738411706-bfc8e691d1c2"],
        "description_es": "Edición de 25. Tallada en madera de cedro rojo, impresa a mano sobre papel washi.",
        "description_en": "Edition of 25. Carved in red cedar, hand-printed on washi paper.",
    },
    {
        "slug": "patio-sur-iv", "artist": "mariana-quiroz",
        "title_es": "Patio sur IV", "title_en": "South Courtyard IV",
        "year": 2025, "medium_es": "Óleo sobre lino", "medium_en": "Oil on linen",
        "dimensions": "150 × 120 cm", "price": "62000", "availability": "available",
        "featured": False, "tags": ["pintura", "abstracto", "luz"],
        "images": ["1578926375605-eaf7559b1458", "1547826039-bfc35e0f1ea8"],
        "description_es": "Continuación de la serie. Pieza de mayor formato que abandona la figura por completo.",
        "description_en": "Continuation of the series. A larger-format piece that abandons figuration entirely.",
    },
    {
        "slug": "travertino-bloque", "artist": "ernesto-vela",
        "title_es": "Travertino, bloque I", "title_en": "Travertine, Block I",
        "year": 2023, "medium_es": "Travertino de Tepeaca", "medium_en": "Tepeaca travertine",
        "dimensions": "60 × 40 × 30 cm", "price": "78000", "availability": "nfs",
        "featured": False, "tags": ["escultura", "piedra"],
        "images": ["1578321272176-b7bbc0679853", "1605000797499-95a51c5269ae"],
        "description_es": "Pieza prestada por el coleccionista para exhibición. No disponible para venta.",
        "description_en": "On loan from the collector for exhibition. Not for sale.",
    },
    {
        "slug": "tianguis-domingo", "artist": "sofia-marin",
        "title_es": "Tianguis, domingo", "title_en": "Tianguis, Sunday",
        "year": 2024, "medium_es": "Fotografía analógica", "medium_en": "Analog photograph",
        "dimensions": "40 × 30 cm", "price": "11000", "availability": "available",
        "featured": False, "tags": ["fotografia", "documental"],
        "images": ["1521714161819-15534968fc5f", "1551892374-ecf8754cf8b0"],
        "description_es": "Tianguis dominical en San Ángel. Edición de 10 + 2 PA.",
        "description_en": "Sunday market in San Ángel. Edition of 10 + 2 AP.",
    },
    {
        "slug": "anil-paisaje", "artist": "luciana-pacheco",
        "title_es": "Añil, paisaje", "title_en": "Indigo, Landscape",
        "year": 2024, "medium_es": "Algodón teñido con añil", "medium_en": "Indigo-dyed cotton",
        "dimensions": "120 × 90 cm", "price": "18500", "availability": "available",
        "featured": False, "tags": ["textil", "tinte-natural"],
        "images": ["1556139943-4bdca53adf1e", "1549887534-1541e9326642"],
        "description_es": "Composición geométrica resuelta en tres tonos de añil, sobre fondo crudo.",
        "description_en": "Geometric composition in three shades of indigo on raw cotton.",
    },
    {
        "slug": "litografia-volcanes", "artist": "tomas-iturbide",
        "title_es": "Volcanes, litografía", "title_en": "Volcanoes, Lithograph",
        "year": 2025, "medium_es": "Litografía sobre piedra", "medium_en": "Stone lithograph",
        "dimensions": "56 × 76 cm", "price": "8200", "availability": "available",
        "featured": False, "tags": ["grabado", "obra-sobre-papel"],
        "images": ["1582738411706-bfc8e691d1c2", "1579783902614-a3fb3927b6a5"],
        "description_es": "Vista del Iztaccíhuatl desde la carretera federal. Edición de 30.",
        "description_en": "View of Iztaccíhuatl from the federal highway. Edition of 30.",
    },
    {
        "slug": "ceramica-cuenco", "artist": "diego-resendiz",
        "title_es": "Cuenco, esmalte mate", "title_en": "Bowl, Matte Glaze",
        "year": 2025, "medium_es": "Gres con esmalte mate", "medium_en": "Stoneware with matte glaze",
        "dimensions": "18 × 28 × 28 cm", "price": "4200", "availability": "available",
        "featured": False, "tags": ["ceramica", "objeto"],
        "images": ["1610701596007-11502861dcfa", "1578321272176-b7bbc0679853"],
        "description_es": "Pieza utilitaria. Cocción a alta temperatura. Apto para uso alimentario.",
        "description_en": "Utilitarian piece. High-temperature firing. Food-safe.",
    },
]


# Starting SEO copy for the curator-managed slots. The `default` fills every page
# not overridden below; page rows only set what differs.
PAGE_SEO = {
    "default": {
        "title_es": "Arte Colibrí — Arte curado de artistas locales",
        "title_en": "Arte Colibrí — Curated art from local artists",
        "description_es": (
            "Una galería digital de arte curado de artistas locales de la Ciudad "
            "de México. Descubre y consulta obra original."
        ),
        "description_en": (
            "A digital gallery of curated art from local artists in Mexico City. "
            "Discover and inquire about original work."
        ),
    },
    "home": {
        "title_es": "Arte Colibrí — Arte curado de artistas locales de la CDMX",
        "title_en": "Arte Colibrí — Curated art from local Mexico City artists",
    },
    "gallery": {
        "title_es": "Galería — Arte Colibrí",
        "title_en": "Gallery — Arte Colibrí",
        "description_es": "Explora la obra publicada de artistas locales de la CDMX.",
        "description_en": "Browse published work from local Mexico City artists.",
    },
    "artists": {
        "title_es": "Artistas — Arte Colibrí",
        "title_en": "Artists — Arte Colibrí",
        "description_es": "Conoce a los artistas en la colección de Arte Colibrí.",
        "description_en": "Meet the artists in the Arte Colibrí collection.",
    },
    "locations": {
        "title_es": "Explorar por ubicación — Arte Colibrí",
        "title_en": "Browse by location — Arte Colibrí",
        "description_es": "Descubre obra por zona de la Ciudad de México.",
        "description_en": "Discover work by Mexico City neighborhood.",
    },
}


class Command(BaseCommand):
    help = "Seed roles, a demo curator/artist, and the prototype catalog."

    @transaction.atomic
    def handle(self, *args, **options):
        artist_group, _ = Group.objects.get_or_create(name=settings.ARTIST_GROUP)
        curator_group, _ = Group.objects.get_or_create(name=settings.CURATOR_GROUP)
        self.stdout.write("Roles ready: Artist, Curator")

        # Demo curator
        curator, created = User.objects.get_or_create(
            username="curador@artecolibri.mx",
            defaults={"email": "curador@artecolibri.mx", "first_name": "Curaduría"},
        )
        if created:
            curator.set_password("colibri123")
            curator.save()
        curator.groups.add(curator_group)

        # Regions & tags
        regions = {}
        for slug, es, en, order in REGIONS:
            regions[slug], _ = Region.objects.update_or_create(
                slug=slug, defaults={"name_es": es, "name_en": en, "order": order}
            )
        tags = {}
        for slug, es, en in TAGS:
            tags[slug], _ = Tag.objects.update_or_create(
                slug=slug, defaults={"label_es": es, "label_en": en}
            )

        # Artists (each with a login user, published)
        artists = {}
        for a in ARTISTS:
            user, created = User.objects.get_or_create(
                username=f"{a['slug']}@artecolibri.mx",
                defaults={"email": f"{a['slug']}@artecolibri.mx", "first_name": a["name"]},
            )
            if created:
                user.set_password("colibri123")
                user.save()
            user.groups.add(artist_group)
            artist, _ = Artist.objects.update_or_create(
                slug=a["slug"],
                defaults={
                    "user": user,
                    "display_name": a["name"],
                    "city": a["city"],
                    "region": regions[a["region"]],
                    "discipline_es": a["discipline_es"],
                    "discipline_en": a["discipline_en"],
                    "bio_es": a["bio_es"],
                    "bio_en": a["bio_en"],
                    "web": a["web"],
                    "instagram": a["instagram"],
                    "since": a["since"],
                    "status": ModerationStatus.PUBLISHED,
                },
            )
            artists[a["slug"]] = artist

        # Artworks + images (published)
        for w in ARTWORKS:
            dims = _parse_dims(w["dimensions"])  # "W × H [× D] cm" → numbers
            artwork, _ = Artwork.objects.update_or_create(
                slug=w["slug"],
                defaults={
                    "artist": artists[w["artist"]],
                    "title_es": w["title_es"],
                    "title_en": w["title_en"],
                    "year": w["year"],
                    "medium_es": w["medium_es"],
                    "medium_en": w["medium_en"],
                    "width": dims.get("width"),
                    "height": dims.get("height"),
                    "depth": dims.get("depth"),
                    "price": Decimal(w["price"]) if w["price"] else None,
                    "availability": w["availability"],
                    "featured": w["featured"],
                    "description_es": w["description_es"],
                    "description_en": w["description_en"],
                    "status": ModerationStatus.PUBLISHED,
                },
            )
            artwork.tags.set([tags[t] for t in w["tags"]])
            artwork.images.all().delete()
            for i, photo_id in enumerate(w["images"]):
                ArtworkImage.objects.create(
                    artwork=artwork,
                    external_url=uns(photo_id),
                    position=i,
                    is_primary=(i == 0),
                )

        # Page SEO slots (create-if-missing so curator edits are never overwritten).
        for key, defaults in PAGE_SEO.items():
            PageSeo.objects.get_or_create(key=key, defaults=defaults)
        self.stdout.write("Page SEO slots ready.")

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(ARTISTS)} artists, {len(ARTWORKS)} artworks. "
                "Curator: curador@artecolibri.mx / colibri123. "
                "Artist demo: mariana-quiroz@artecolibri.mx / colibri123."
            )
        )

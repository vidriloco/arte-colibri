from django.contrib import admin

from world.models import Artist, Artwork, ArtworkImage, Inquiry, Region, Tag


class ArtworkImageInline(admin.TabularInline):
    model = ArtworkImage
    extra = 0


@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ("display_name", "city", "region", "status", "user")
    list_filter = ("status", "region")
    search_fields = ("display_name", "slug")
    prepopulated_fields = {"slug": ("display_name",)}


@admin.register(Artwork)
class ArtworkAdmin(admin.ModelAdmin):
    list_display = ("title_es", "artist", "year", "availability", "status", "featured")
    list_filter = ("status", "featured", "availability", "tags")
    search_fields = ("title_es", "title_en", "slug")
    autocomplete_fields = ("artist",)
    filter_horizontal = ("tags",)
    inlines = [ArtworkImageInline]


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "artwork", "created_at")
    search_fields = ("name", "email")


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ("name_es", "slug", "order")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("label_es", "slug")

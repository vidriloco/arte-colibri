## 1. Data model & migration (`geodjango/world`)

- [x] 1.1 Add `PageSeo` model (`key` enum, bilingual title/description, bilingual OG title/description, `og_image`, `canonical`, `robots`, `updated_by/at`) with `resolve(key)` per-field fallback to `default` + built-in site defaults
- [x] 1.2 Register in `world/models/__init__.py`; generate migration
- [x] 1.3 Seed the `default` + 4 page rows in `seed_demo` (idempotent)

## 2. API (serializers, views, URLs)

- [x] 2.1 `PageSeoSerializer` (curator R/W; bilingual via `BilingualField`; `og_image`, `canonical`, `robots`)
- [x] 2.2 `PublicSeoView` — resolved SEO for a page key (bilingual shape, absolute OG image URL)
- [x] 2.3 `CurationSeoViewSet` (`IsCurator`) — list/retrieve/update slots + OG-image upload action
- [x] 2.4 Wire routes in `world/api/urls.py`

## 3. Server-side shell injection

- [x] 3.1 `world/seo.py`: `page_key_for_path`, `seo_for_request` (managed slots + content-derived detail meta), `render_head`, `inject_seo` (pure)
- [x] 3.2 `AppShellView` serving the SPA shell (built `dist/index.html`, cached in prod) with injected head
- [x] 3.3 Catch-all route in `geodjango/urls.py` → `AppShellView` (excluding `api/`, `admin/`, `media/`, `static/`)
- [x] 3.4 Settings: WhiteNoise for built assets, `STATIC_ROOT`/`STATICFILES_DIRS`, `SPA_INDEX_HTML`; read `DEBUG`/`ALLOWED_HOSTS` from env; add `whitenoise` to requirements; Vite `base:/static/` for prod build

## 4. Frontend

- [x] 4.1 `head.js` head manager + `useHead` hook; apply resolved SEO per route + language
- [x] 4.2 Wire the 7 screens (managed pages fetch their slot; detail pages derive from loaded content)
- [x] 4.3 `api.js`: `Public.seo`, `Curation.seo/saveSeo/uploadSeoImage`; i18n strings (ES/EN)
- [x] 4.4 SEO tab in the curator dashboard (`dashboard/SeoTab.jsx`) — per-slot editor with the full field set + OG image upload/preview

## 5. Tests & docs

- [x] 5.1 Resolution fallback (page → default → site) + bilingual shape
- [x] 5.2 Curator can update; non-curator/anon rejected (403/401)
- [x] 5.3 `inject_seo` output (title/description/robots/OG) + duplicate-title stripping
- [x] 5.4 `AppShellView` injects the managed title for `/gallery`; noindex honored; detail route derives from content
- [x] 5.5 README: managing SEO from the dashboard + prod build/serve note

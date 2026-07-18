## 1. Dependencies & settings

- [ ] 1.1 Add `djangorestframework`, `django-cors-headers` (and confirm `Pillow`) to `requirements.txt`
- [ ] 1.2 Add `rest_framework`, `rest_framework.authtoken`, `corsheaders` to `INSTALLED_APPS`; add corsheaders middleware
- [ ] 1.3 Add `REST_FRAMEWORK` config (token + session auth, default pagination, page size) and `CORS_ALLOWED_ORIGINS` (Vite dev origin + prod origin)
- [ ] 1.4 Configure `MEDIA_URL`/`MEDIA_ROOT`; serve media in `DEBUG`; run the `authtoken` migration

## 2. Serializers (per audience)

- [ ] 2.1 Bilingual field helper that serializes `*_es`/`*_en` pairs into `{es, en}`
- [ ] 2.2 Public serializers: ArtworkList, ArtworkDetail (ordered images, primary first), ArtistPublic (+ published works), RegionGroup
- [ ] 2.3 Dashboard serializers: ArtworkOwner (status + ownership fields, write), ArtistOwner (profile write), ArtworkImage (upload/order/primary)
- [ ] 2.4 Curator serializers: review-queue + review fields (`reviewed_by`, `reviewed_at`, `review_notes`); Inquiry serializer
- [ ] 2.5 Auth serializers: signup (name/email/password), login, current-user (role + linked artist)

## 3. Permissions

- [ ] 3.1 `IsOwnerArtist` object permission (artist owns the artwork/profile)
- [ ] 3.2 `IsCurator` permission (in `Curator` group or admin)
- [ ] 3.3 Guard against self-publish/self-feature on the owner write paths

## 4. Public read endpoints (published-only)

- [ ] 4.1 Home feed (featured-first then recent) from `Artwork.published`
- [ ] 4.2 Gallery list with `tag` filter (AND), `sort` (recent/price_asc/price_desc), page-number pagination
- [ ] 4.3 Artwork detail by slug/id — 404 if not published
- [ ] 4.4 Artist detail by slug — 404 if not published; include only published works
- [ ] 4.5 Works-grouped-by-region endpoint (omit empty regions, include counts)
- [ ] 4.6 Tags/regions metadata endpoint for filter UI

## 5. Auth & signup

- [ ] 5.1 Signup endpoint: create user in `Artist` group + linked unpublished `Artist`; return token
- [ ] 5.2 Login/logout endpoints; token issue
- [ ] 5.3 `/api/auth/me` returning identity, role, linked artist

## 6. Dashboard endpoints (owner-scoped)

- [ ] 6.1 Artist profile read/update (own only)
- [ ] 6.2 Artwork CRUD scoped to owner; reject cross-owner access (403/404)
- [ ] 6.3 Image upload (multipart) + reorder + set-primary; first upload becomes primary; non-image rejected
- [ ] 6.4 Submit-for-review action (`draft`→`submitted`)
- [ ] 6.5 Artist inquiries inbox (own works only)

## 7. Curation endpoints (curator-only)

- [ ] 7.1 Review queue (submitted artworks + profiles)
- [ ] 7.2 Approve action (`submitted`→`published`)
- [ ] 7.3 Reject-with-notes action (notes required; `submitted`→`rejected`; record reviewer/timestamp)
- [ ] 7.4 Feature action (published only)
- [ ] 7.5 All-inquiries inbox

## 8. Inquiries

- [ ] 8.1 Inquiry submission endpoint against a published artwork; validate email; record against artwork+artist; 404 if artwork not published

## 9. URLs & wiring

- [ ] 9.1 `world/api/urls.py` with routers/paths; mount at `/api/` in `geodjango/urls.py`

## 10. Tests

- [ ] 10.1 Visibility gating: every public route returns only published; non-published id → 404
- [ ] 10.2 Field exposure: dashboard/curator-only fields never appear in public responses; bilingual fields shaped as `{es,en}`
- [ ] 10.3 Auth: signup creates Artist-group user + profile + token; login token works; `/me` role correct; duplicate email → 400
- [ ] 10.4 Ownership: artist can edit only own; cannot self-publish/feature (403)
- [ ] 10.5 Curation: approve/reject/feature transitions; reject requires notes; feature requires published; non-curator → 403
- [ ] 10.6 Images: first upload primary, primary switch, non-image rejected
- [ ] 10.7 Inquiry: valid recorded (201), invalid email → 400, unpublished artwork → 404
- [ ] 10.8 Gallery: tag filter (AND), sort variants, pagination metadata

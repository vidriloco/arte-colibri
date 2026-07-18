## 1. Data model & migrations (`geodjango/world`)

- [ ] 1.1 Add `Artist` model (slug, display_name, bio/statement, avatar ImageField, links, city, region, optional PointField) linked one-to-one to `auth.User`
- [ ] 1.2 Add `Artwork` model (FK→Artist, title, slug unique-per-artist, description, medium, dimensions, year, price Decimal, currency, availability enum, tags)
- [ ] 1.3 Add `ArtworkImage` model (FK→Artwork, image, position, is_primary) with image validation
- [ ] 1.4 Add `Inquiry` model (FK→Artwork, visitor name/email, message, created_at)
- [ ] 1.5 Add moderation fields (`status`, `featured`, `featured_order`, `reviewed_by`, `reviewed_at`, `review_notes`) to `Artwork` and `Artist`
- [ ] 1.6 Add a `published` manager/queryset and a `featured` helper on `Artwork`
- [ ] 1.7 Generate and apply migrations

## 2. Auth, roles & media

- [ ] 2.1 Add `Pillow` to requirements.txt and configure `MEDIA_ROOT` / `MEDIA_URL`
- [ ] 2.2 Add a persistent media volume to docker-compose (base) + serve media in dev; document prod storage (django-storages follow-up)
- [ ] 2.3 Data migration / management command to create `Artist` and `Curator` groups with permissions and seed an initial curator
- [ ] 2.4 Add reusable permission helpers/mixins (owner-only and curator-only access checks)

## 3. Curation workflow

- [ ] 3.1 Implement status transitions: submit (`draft`→`submitted`), approve (`submitted`→`published`), reject (`submitted`→`rejected`, notes required)
- [ ] 3.2 Enforce that only owners can submit and only curators/admins can approve/reject/feature
- [ ] 3.3 Generate thumbnails on image upload (Pillow)

## 4. Public showcase (templates + views)

- [ ] 4.1 Replace placeholder `index` with the new home page (identity hero + featured-then-recent grid + empty state)
- [ ] 4.2 Gallery page (published list, primary image/title/artist/price, pagination, tag filter)
- [ ] 4.3 Artwork detail page (images, details, price, availability label, Inquire action — no cart/checkout)
- [ ] 4.4 Artist profile page (published profiles only; lists artist's published works)
- [ ] 4.5 Browse-by-location section (group published works by artist region; secondary placement)
- [ ] 4.6 Wire all public views through the `published` manager; add URLs
- [ ] 4.7 SEO/meta for home + detail pages reflecting the curated-local-artists identity

## 5. Inquiries

- [ ] 5.1 Inquiry form + view on the artwork detail page with validation
- [ ] 5.2 Record inquiries against artwork + artist; show confirmation

## 6. Management dashboard (`/dashboard`)

- [ ] 6.1 Dashboard shell + login-required + role-based routing (Artist vs Curator/admin)
- [ ] 6.2 Artist: edit own profile + submit for review
- [ ] 6.3 Artist: artwork CRUD, image upload/ordering, price/availability/tags, submit for review (no self-publish/feature)
- [ ] 6.4 Curator: review queue with approve / reject-with-notes / feature actions
- [ ] 6.5 Inquiries inbox (artist sees own; curator sees all)

## 7. Tests

- [ ] 7.1 Visibility gating: unpublished artworks/profiles return 404 publicly; public queries return only published
- [ ] 7.2 Curation: submit/approve/reject transitions, reject requires notes, feature requires published, role enforcement
- [ ] 7.3 Ownership: artists can edit only their own content; cannot self-publish
- [ ] 7.4 Artwork images: first image primary, primary switch, non-image rejected
- [ ] 7.5 Inquiry: valid submission recorded + visible in inbox; invalid email rejected
- [ ] 7.6 Home page: identity copy present, featured ordered first, empty state renders

## 8. Documentation

- [ ] 8.1 Document the data model, roles, and curation flow in the README/dashboard guide
- [ ] 8.2 Note media-storage requirements (dev volume now, object storage as follow-up)

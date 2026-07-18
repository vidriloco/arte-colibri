## 1. Scaffold & tooling

- [ ] 1.1 Create `frontend/` Vite + React 18 project (`package.json`, entry, index.html)
- [ ] 1.2 Configure dev server proxy for `/api` and `/media` → Django; set API base URL via env
- [ ] 1.3 Add subsetted Google Fonts (Fraunces, Inter, JetBrains Mono) and load the design CSS

## 2. Design system & shell

- [ ] 2.1 Port the bespoke `styles.css` design system (tokens, typography, components) for the Galería direction
- [ ] 2.2 App shell: layout, Nav (logo, links, language toggle, sign-in/apply), Footer
- [ ] 2.3 Shared components: ArtworkCard (+ featured variant), StatusBadge, FilterChips, ArtImage with striped fallback, Crumbs, buttons
- [ ] 2.4 Shared states: loading, empty, error, 404

## 3. Routing, i18n, auth, API client

- [ ] 3.1 React Router routes: `/`, `/gallery`, `/artwork/:slug`, `/artist/:slug`, `/artists`, `/locations`, `/dashboard/*`, catch-all 404; scroll-to-top on navigation
- [ ] 3.2 i18n: port `DICT`, language context + `t()` helper, ES default, nav toggle, persist to localStorage; render API `{es,en}` fields
- [ ] 3.3 API client: base URL, auth header, JSON + multipart, error normalization
- [ ] 3.4 Auth context from `/api/auth/me`; route guards for `/dashboard/*`; artist vs curator routing

## 4. Public showcase screens

- [ ] 4.1 Home: full-bleed showcase carousel hero (5 recent, cross-fade, counter, arrows, keyboard nav, auto-advance + pause-on-hover, progress ticks) over brand identity
- [ ] 4.2 Home: featured-first then recent grid + browse-by-location teaser + empty state
- [ ] 4.3 Gallery: card grid, tag filter chips, sort, pagination, no-results empty state
- [ ] 4.4 Artwork detail: primary image + thumbnail strip, specs, price + availability badge, tags
- [ ] 4.5 Inquire modal: name/email/message, validation, success state, posts to API; sold disables inquire
- [ ] 4.6 Artist profile: identity, statement, links, grid of published works
- [ ] 4.7 Artists listing (roster/grid) → profile links
- [ ] 4.8 Browse-by-location: grouped-by-region with counts; 404/unavailable states for missing/unpublished detail/profile

## 5. Artist application / signup flow

- [ ] 5.1 Account step: name/email/password+confirm/terms with validation
- [ ] 5.2 Onboarding dashboard: profile + first-artwork task cards, progress, gated submit
- [ ] 5.3 Profile task form and artwork task form (with image upload) wired to the API
- [ ] 5.4 Submission success state (received · 5 business days; submit-another / return-home)

## 6. Management dashboard

- [ ] 6.1 Dashboard shell + role-based view selection (artist vs curator)
- [ ] 6.2 Artist: own-artworks list with status badges
- [ ] 6.3 Artist: artwork create/edit form — images (upload/reorder/primary), medium, dimensions, year, price/NFS, tags, bilingual title/description
- [ ] 6.4 Artist: submit-for-review action; edit own profile
- [ ] 6.5 Curator: review queue with approve / reject-with-notes (required) / feature (published only)
- [ ] 6.6 Inquiries inbox: artist scoped to own works; curator sees all

## 7. Integration, build & docs

- [ ] 7.1 Docker: SPA build step/service; dev proxy; reuse media volume; prod static serving
- [ ] 7.2 Update `openspec/config.yaml` project context to React SPA + DRF API
- [ ] 7.3 README: how to run the SPA (dev + build) alongside the API
- [ ] 7.4 Note the SEO/prerender follow-up for public routes

## 8. Verification

- [ ] 8.1 Smoke-run the SPA against the API: navigate every public screen, inquire, sign up, artist CRUD + submit, curator approve/reject/feature
- [ ] 8.2 Verify bilingual toggle switches all UI + domain copy and persists
- [ ] 8.3 Verify visibility gating from the UI: no unpublished content reachable; 404 states render

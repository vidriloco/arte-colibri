## Why

A design handoff from Claude Design delivered a fully interactive prototype of Arte Colibrí built in React, and the product owner has chosen to ship the frontend as a ReactJS single-page app. This **overrides the earlier "server-rendered Django templates + Bootstrap, no SPA framework" decision**. The SPA will recreate the approved design pixel-faithfully and consume the JSON contract from the companion `json-content-api` change. Everything must be bilingual (Spanish-first with an English toggle).

## What Changes

- **BREAKING (architecture):** the frontend is a ReactJS SPA built with Vite, not Django templates. The placeholder `index` page and the "no SPA" convention are retired.
- Establish the **SPA shell**: build tooling (Vite + React), client-side routing for every screen, an auth/session context (signup/login/logout, role awareness), an API client targeting `/api/`, the ported design system (tokens, fonts, components), and shared loading / empty / error / 404 states.
- **Bilingual i18n (ES/EN)** across all UI strings, with a language toggle in the nav; bilingual domain copy (artwork title/medium/description, artist bio/discipline) rendered from the API's `{es,en}` fields. Spanish is the default.
- Build the **public showcase screens** exactly as designed: Home with a full-bleed **showcase carousel hero** of the 5 most recent works (auto-advance, keyboard nav, progress ticks) over the brand identity, plus a featured/editorial grid, recent grid, and a browse-by-location teaser; **Gallery** with tag filter chips, sort, and pagination; **Artwork detail** with an image thumbnail strip, specs, price + availability badge, and an **Inquire** modal (name/email/message, validation, success state — no cart/checkout); **Artist profile**; **Artists** roster/grid; **Browse by location**; and graceful **empty / 404** states.
- Build the **artist application / signup flow** as designed: account creation → onboarding dashboard with profile + first-artwork tasks → submission success ("recibido · te contactamos en 5 días hábiles").
- Build the **management dashboard**: artist view (own artworks with Draft/Submitted/Published/Rejected status badges, artwork CRUD with multi-image upload + ordering, submit-for-review, edit profile, inquiries inbox) and curator view (review queue with approve / reject-with-notes / feature, access to all content, all inquiries).
- Apply the **brand visual system**: warm gallery off-white `#FAF8F4` canvas, near-black `#1B1A17` ink, teal-green `#117360` primary accent, magenta `#E0457B` used sparingly, hairline `#E7E2DA`; Fraunces (headings) + Inter (UI) + JetBrains Mono (metadata).

## Capabilities

### New Capabilities
- `react-spa`: the SPA foundation — Vite/React build & dev/proxy setup, client-side routing for all screens, bilingual i18n (ES/EN) with a toggle, auth/session context and route guards, the API client, the ported design system/tokens/typography, and shared loading/empty/error/404 states.
- `public-showcase-ui`: the visitor-facing screens — home (showcase carousel hero + featured/recent grids + locations teaser), gallery (filter/sort/pagination), artwork detail (+ inquire modal), artist profile, artists roster/grid, browse-by-location, empty/404.
- `dashboard-ui`: the authenticated screens — artist application/signup flow, artist dashboard (own works + status badges + artwork CRUD with image upload/ordering + submit + profile edit + inquiries inbox), and curator dashboard (review queue + approve/reject/feature + all content + all inquiries).

### Modified Capabilities
<!-- Baseline specs (openspec/specs/) are empty; artist-showcase-mvp is not yet archived, so there are no baseline requirements to MODIFY. The shift away from server-rendered templates is recorded as a Decision in design.md and in the updated openspec/config.yaml context. -->
- None.

## Impact

- **New frontend project** (e.g. `frontend/`): Vite + React app, `package.json`, design-system CSS ported from the prototype, i18n dictionary, router, API client, and all screen/dashboard components. Node 24 toolchain.
- **Consumes** `json-content-api` for all data, auth, uploads, and curation actions; **depends on** `artist-showcase-mvp` for the domain semantics.
- **Infra/Docker**: a build step or service for the SPA (dev: Vite server proxying `/api` to Django; prod: built static assets served by Django/nginx) plus the media volume from the API change.
- **Conventions**: update `openspec/config.yaml` project context — the frontend is now a React SPA over a DRF JSON API, not server-rendered templates.
- **SEO**: a SPA is not server-rendered, so crawlable HTML/metadata for the home and detail pages becomes a prerender/SSR follow-up; the repo's prior SEO work and `seo-audit` skill should inform that fast-follow.

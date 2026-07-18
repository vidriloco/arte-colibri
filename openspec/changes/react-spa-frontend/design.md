## Context

A Claude Design handoff produced a complete, interactive React prototype of Arte Colibrí (single HTML file loading React + Babel, with `data.jsx`, `components.jsx`, `screens.jsx`, `showcase-carousel.jsx`, `apply-modal.jsx`, and a ~3.5k-line bespoke `styles.css`). The product owner chose to ship the frontend as a ReactJS SPA, overriding the earlier "server-rendered Django templates, no SPA" decision in `artist-showcase-mvp`/`openspec/config.yaml`. This change designs how the prototype becomes a production SPA over the `json-content-api` contract, bilingual end to end.

The prototype's `styles.css` is framework-agnostic vanilla CSS using custom properties — it ports directly and is the source of visual truth. The prototype also includes design-exploration scaffolding (a Tweaks panel; three aesthetic "directions" Galería/Estudio/Códice) that are tools, not product features.

## Goals / Non-Goals

**Goals:**
- Recreate the approved design pixel-faithfully by porting the prototype's bespoke CSS design system.
- A maintainable SPA: real component structure, client-side routing, an auth context, and a typed-ish API client — replacing the prototype's `window`-global, Babel-in-browser approach.
- Bilingual ES/EN across all UI, default Spanish, with a nav toggle; domain copy rendered from the API's `{es,en}` fields.
- Every screen from the brief: public showcase, the artist apply/signup flow, and the artist + curator management dashboard.
- Inquire-only commerce (price display + inquiry modal); no cart/checkout anywhere.

**Non-Goals:**
- The JSON API, models, curation state machine, or auth backend (owned by `json-content-api` + `artist-showcase-mvp`).
- Shipping the Tweaks panel and the three aesthetic directions as product features — only the primary **Galería** direction ships (teal accent, Fraunces). Tokens are kept so alternates could return later.
- Server-side rendering / prerendering for SEO (flagged as a follow-up).
- Native mobile apps.

## Decisions

- **Vite + React 18.** Fast dev server with HMR and a simple production build; replaces the prototype's in-browser Babel. *Alternatives:* Next.js (brings SSR/routing but heavier and implies a Node server in prod — deferred with SSR) or CRA (unmaintained) — rejected.
- **Port the bespoke design system verbatim.** Bring `styles.css` over as the design foundation (tokens, typography, components) rather than rebuilding on Bootstrap. The brief's "implementable in Bootstrap" note is satisfied structurally (12-col-style grids, cards, modals), but the *approved* look is the bespoke CSS, so pixel-faithfulness means porting it. *Alternative:* rebuild with Bootstrap components — rejected as not pixel-faithful to what the user approved.
- **Ship only the Galería direction.** The Estudio/Códice directions and the Tweaks panel were design-exploration; production ships the canonical Galería aesthetic. Keep CSS custom properties so a direction switch could be reintroduced.
- **i18n via a lightweight dictionary + context** (port the prototype's `DICT`), default `es`, toggle in nav, selection persisted (localStorage). Domain copy comes from API `{es,en}` objects; a small `t(field, lang)` helper picks the active language. *Alternative:* `react-i18next` — viable, but the prototype's flat dictionary is sufficient for MVP and avoids extra config.
- **Routing with React Router.** Routes for `/` (home), `/gallery`, `/artwork/:slug`, `/artist/:slug`, `/artists`, `/locations`, `/dashboard/*`, and a catch-all 404. The Inquire and Apply experiences are modals layered over the current route. Scroll-to-top on navigation. *Alternative:* the prototype's single-`useState` screen switch — rejected (no URLs, no deep links, no back button).
- **Auth context + route guards.** A context exposes the current user/role/token (from `/api/auth/me`), gates `/dashboard/*`, and routes artists vs curators to their respective dashboard views. Token stored client-side; attached by the API client.
- **API client module** centralizes base URL, auth header, JSON/multipart handling, and error normalization; screens call typed functions, not raw fetch. Loading/empty/error states are shared components.
- **Image fallback** preserved from the prototype: on image load error, render the striped-SVG placeholder with a monospace label, so missing media never breaks layout.
- **Dev/prod serving.** Dev: Vite dev server proxies `/api` and `/media` to Django (CORS also configured on the API side). Prod: `vite build` static assets served by Django/nginx; a Docker step builds the SPA. The home/detail SEO gap is acknowledged for a prerender follow-up.

## Risks / Trade-offs

- **SEO regression** (no server-rendered HTML) → acknowledged; plan a prerender/SSR follow-up; keep route-level metadata in the SPA in the interim.
- **API/SPA contract drift** → the `{es,en}` bilingual shape and endpoint list in `json-content-api` are the source of truth; ship both changes together; cover the client with integration-level checks against a running API.
- **Pixel fidelity loss when porting** → bring `styles.css` over wholesale and match the prototype's DOM structure/class names so the CSS applies unchanged.
- **Auth/CORS friction across origins in dev** → use token auth from the SPA and pin `CORS_ALLOWED_ORIGINS`; document the dev workflow.
- **Scope size** → order work so the SPA shell + public showcase ship before the dashboard; the dashboard can start with core flows and grow. The apply flow ships its primary (dashboard-with-tasks) variant only; the wizard/single-page variants from the prototype are not product requirements.
- **Large bundle from fonts/CSS** → subset Google Fonts to the weights used; the single bespoke stylesheet keeps CSS small.

## Migration Plan

- Add the `frontend/` Vite project; no impact on existing Django until cutover.
- Wire dev proxy (`/api`, `/media` → Django) and confirm against `json-content-api`.
- Cutover: replace the placeholder `index` experience with the SPA entry; keep `/` serving the app.
- Docker: add a build step/service for the SPA; reuse the media volume from `json-content-api`.
- Update `openspec/config.yaml` project context to describe the React SPA + DRF API architecture.
- Rollback: the Django API is unaffected; revert the frontend serving to the placeholder if needed.

## Open Questions

- **Prerender/SSR for SEO** — which approach (static prerender of public routes vs. adopting Next.js later)? Deferred.
- **Hosting of built assets** — Django `collectstatic`/WhiteNoise vs. nginx vs. CDN. MVP: served alongside Django; revisit for scale.
- **Persisting language choice** — localStorage for MVP; consider `Accept-Language`/profile preference later.
- **Apply-flow account provisioning** — relies on `json-content-api` self-signup (overrides invite-only); confirm anti-abuse (captcha/throttle) need before public launch.

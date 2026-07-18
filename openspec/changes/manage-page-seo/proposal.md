## Why

Arte Colibrí's frontend is a ReactJS SPA (`react-spa-frontend`). A pure client-side
SPA is a problem for SEO and link sharing: the initial HTML that Django/Vite serves
carries a single hard-coded `<title>`/`<meta name="description">` for every route, and
meta tags set later by React are **not** seen by social/link-preview scrapers
(WhatsApp, Facebook, X, LinkedIn) or by crawlers that don't execute JS. There is also
no way for the team to tune this copy without editing code.

This change makes the SEO metadata of the main public pages **editable from the curator
dashboard** and **delivered server-side**, so the values a curator sets are present in
the first HTML response for both search engines and link-preview scrapers.

## What Changes

- Introduce a **`PageSeo`** record, curator-managed, for a fixed set of key pages —
  **Home, Gallery, Artists, Browse-by-location** — plus a site-wide **`default`** slot
  used as a per-field fallback.
- Each slot carries the **full field set**: bilingual (`{es,en}`) meta **title** and
  **description**, bilingual **Open Graph** title/description, a shared **OG image**,
  a **canonical** override, and a **robots** directive.
- Add **curator-only API endpoints** to read and update the slots (and upload the OG
  image), and a **public read endpoint** returning the *resolved* SEO for a page (page
  value → `default` value → built-in default), for the SPA to apply on client-side
  navigation and language toggle.
- **Server-inject** the resolved meta: Django serves the SPA's HTML shell for public
  routes and splices the correct `<head>` (title, description, canonical, robots,
  OG/Twitter tags, `<html lang>`) into the initial document. Detail routes
  (`/artwork/:slug`, `/artist/:slug`) are **not** dashboard slots but receive meta
  auto-derived from the published item (title, description, primary image), falling
  back to the `default` slot. This requires Django to serve the built SPA — closing
  most of the standing "SPA is not server-rendered / no prod serving" follow-up.
- Add a **SEO** tab to the **curator dashboard** to edit every slot, and a client-side
  **head manager** that keeps `<title>`/meta in sync during SPA navigation.
- Spanish is the server-rendered default language (Spanish-first); the client updates
  the head when the user toggles to English.

## Capabilities

### New Capabilities
- `page-seo`: curator-managed, bilingual, per-page SEO metadata for the key public
  pages — its resolution/fallback rules, the curator read/update + OG-image endpoints,
  the public resolved-SEO endpoint, server-side injection into the SPA shell (including
  content-derived meta for detail routes), and the dashboard editor.

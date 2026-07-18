## ADDED Requirements

### Requirement: Curator-managed per-page SEO records

The system SHALL persist an editable SEO record for a fixed set of page keys —
`home`, `gallery`, `artists`, `locations` — plus a `default` slot. Each record SHALL
carry bilingual (`{es,en}`) meta title and description, bilingual Open Graph title and
description, an OG image, a canonical URL override, and a robots directive. Only users
in the `Curator` group (or admins) SHALL read or write these records; the values SHALL
NOT be writable by artists or anonymous visitors.

#### Scenario: Curator updates a page's SEO

- **WHEN** a curator submits new title/description for the `gallery` slot
- **THEN** the record is saved and subsequent resolution for `gallery` returns the new values

#### Scenario: Non-curator cannot edit SEO

- **WHEN** an artist or anonymous client attempts to read or write the SEO endpoints
- **THEN** the request is rejected with 403 (or 401 if unauthenticated)

### Requirement: SEO resolution with per-field fallback

The system SHALL resolve the effective SEO for a page key by taking each field from the
page's own record, else from the `default` record, else from a built-in site default.
Open Graph title/description SHALL fall back to the plain title/description of the same
resolution. The robots directive SHALL default to `index,follow`.

#### Scenario: Empty page field falls back to default slot

- **WHEN** the `artists` record leaves description blank but the `default` record sets one
- **THEN** the resolved description for `artists` is the `default` record's value

#### Scenario: Bilingual shape is preserved

- **WHEN** a client fetches the resolved SEO for a page
- **THEN** `title`, `description`, `og_title`, and `og_description` are each `{ "es": …, "en": … }`

### Requirement: Server-side injection into the SPA shell

The system SHALL serve the SPA's HTML shell for public routes and inject the resolved
SEO into the initial document `<head>` before it is returned — replacing the static
`<title>`/`<meta name="description">` and adding canonical, robots, Open Graph, and
Twitter card tags, plus the `<html lang>` attribute. Spanish SHALL be the server-rendered
default language.

#### Scenario: Gallery HTML carries the managed title

- **WHEN** a crawler requests `/gallery`
- **THEN** the returned HTML `<title>` and `<meta name="description">` reflect the resolved `gallery` SEO, not the generic shell defaults

#### Scenario: Noindex is honored server-side

- **WHEN** a page's robots directive is `noindex,follow`
- **THEN** the served HTML contains `<meta name="robots" content="noindex,follow">`

### Requirement: Content-derived meta for detail routes

For `/artwork/:slug` and `/artist/:slug`, which are not dashboard-managed slots, the
system SHALL derive the injected meta from the published item — title, description, and
primary image — falling back to the `default` slot when the item is missing or
unpublished.

#### Scenario: Artwork detail uses the artwork's own meta

- **WHEN** a crawler requests a published artwork's detail URL
- **THEN** the injected title/description/OG image reflect that artwork, not the generic default

#### Scenario: Unknown artwork falls back to default

- **WHEN** a crawler requests an artwork slug that is not published
- **THEN** the served HTML uses the `default` slot's resolved SEO (and the SPA renders its 404)

### Requirement: Client-side head synchronization

The SPA SHALL keep the document head in sync during client-side navigation and language
toggling, applying the resolved SEO for the current route (fetched for managed pages,
derived from loaded content for detail pages) so titles and share metadata are correct
after in-app navigation as well as on first load.

#### Scenario: Title updates on SPA navigation

- **WHEN** a user navigates from Home to Gallery within the SPA
- **THEN** `document.title` updates to the Gallery page's resolved title without a full reload

#### Scenario: Language toggle updates the head

- **WHEN** the user switches the language toggle to English
- **THEN** the document title/description update to the English resolution

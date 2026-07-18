## ADDED Requirements

### Requirement: Single-page app shell and routing

The frontend SHALL be a ReactJS single-page application with client-side routing that provides addressable routes for the home, gallery, artwork detail, artist profile, artists list, browse-by-location, and dashboard screens, plus a catch-all 404. Navigating SHALL update the URL (supporting back/forward and deep links) and reset scroll to the top of the new screen.

#### Scenario: Deep link to a screen

- **WHEN** a user opens a URL for a specific artwork
- **THEN** the SPA renders that artwork's detail screen directly without first showing the home screen

#### Scenario: Unknown route shows 404

- **WHEN** a user navigates to a route that does not exist
- **THEN** the SPA renders the 404 state, not a blank page

#### Scenario: Scroll resets on navigation

- **WHEN** a user navigates from one screen to another
- **THEN** the new screen is shown scrolled to the top

### Requirement: Bilingual UI with language toggle

The SPA SHALL render all UI strings in Spanish by default and SHALL provide a language toggle (ES/EN) in the navigation that switches the entire UI and all domain copy without a full page reload. Domain copy SHALL be sourced from the API's bilingual `{es,en}` fields. The selected language SHALL persist across reloads.

#### Scenario: Default language is Spanish

- **WHEN** a first-time visitor loads the app
- **THEN** the UI and copy render in Spanish

#### Scenario: Toggle to English

- **WHEN** the visitor selects EN in the language toggle
- **THEN** all UI labels and bilingual domain copy (titles, mediums, bios) switch to English in place

#### Scenario: Language persists

- **WHEN** a visitor who selected EN reloads the page
- **THEN** the app loads in English

### Requirement: API client and data states

The SPA SHALL fetch all data from the `/api/` JSON contract through a central client that attaches authentication and normalizes errors, and SHALL render explicit loading, empty, and error states for data-backed screens.

#### Scenario: Loading indicator

- **WHEN** a screen's data request is in flight
- **THEN** a loading state is shown until data arrives or an error occurs

#### Scenario: Error state on request failure

- **WHEN** an API request fails
- **THEN** the screen shows a recoverable error state rather than crashing

#### Scenario: Empty state when no published content

- **WHEN** a list endpoint returns no items
- **THEN** the screen shows the designed empty state (not an error)

### Requirement: Authentication context and route guards

The SPA SHALL maintain an authentication context exposing the current user, role (artist vs curator/admin), and credential, hydrated from `/api/auth/me`. Routes under the dashboard SHALL require authentication, redirecting unauthenticated users to sign in, and SHALL route artists and curators to their respective dashboard views.

#### Scenario: Unauthenticated dashboard access

- **WHEN** an unauthenticated user navigates to a dashboard route
- **THEN** they are redirected to sign in / the apply flow

#### Scenario: Role-based dashboard routing

- **WHEN** an authenticated artist and an authenticated curator each open the dashboard
- **THEN** the artist sees the artist view and the curator sees the curator view

#### Scenario: Session persists across reloads

- **WHEN** an authenticated user reloads the app
- **THEN** the auth context rehydrates and keeps them signed in

### Requirement: Ported design system and image fallback

The SPA SHALL apply the brand design system — canvas `#FAF8F4`, ink `#1B1A17`, primary accent teal-green `#117360`, magenta `#E0457B` used sparingly, hairline `#E7E2DA`, with Fraunces (headings), Inter (UI), and JetBrains Mono (metadata) — and SHALL render a striped-placeholder fallback with a label whenever an image fails to load.

#### Scenario: Brand tokens applied

- **WHEN** any screen renders
- **THEN** it uses the brand canvas/ink/accent colors and the Fraunces/Inter/JetBrains Mono type system

#### Scenario: Image fails to load

- **WHEN** an artwork image URL fails to load
- **THEN** a striped SVG placeholder with a text label is shown in its place, preserving layout

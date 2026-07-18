## ADDED Requirements

### Requirement: API mounting and JSON contract

The system SHALL expose a JSON HTTP API rooted at `/api/`. All endpoints SHALL accept and return `application/json` (except image upload, which accepts `multipart/form-data`). Responses SHALL use conventional HTTP status codes (200/201 success, 400 validation, 401 unauthenticated, 403 forbidden, 404 not found).

#### Scenario: API root is namespaced

- **WHEN** any API request is made
- **THEN** it is served under the `/api/` path prefix, separate from the SPA and media routes

#### Scenario: Validation errors are structured

- **WHEN** a write request fails validation
- **THEN** the response is HTTP 400 with a JSON body mapping field names to error messages

### Requirement: Bilingual field payloads

The API SHALL return fields that are bilingual in the domain as nested objects with `es` and `en` keys, so the client can switch language without refetching. Single-language fields (slug, year, dimensions, price, currency, availability, region id) SHALL remain flat.

#### Scenario: Artwork title is bilingual

- **WHEN** a client fetches an artwork
- **THEN** `title`, `medium`, and `description` are each returned as `{ "es": "…", "en": "…" }`

#### Scenario: Artist bio is bilingual

- **WHEN** a client fetches an artist
- **THEN** `bio`/`statement` and `discipline` are returned as `{ "es": "…", "en": "…" }`

### Requirement: Public read endpoints expose only published content

The API SHALL provide unauthenticated read endpoints that return ONLY published content, with the published gate enforced at the queryset layer. The endpoints SHALL include: home feed (featured-first then recent), gallery list, artwork detail, artist detail (with that artist's published works), and works grouped by region.

#### Scenario: Gallery lists only published works

- **WHEN** an unauthenticated client requests the gallery list
- **THEN** the response contains only artworks whose status is `published` and never `draft`, `submitted`, or `rejected`

#### Scenario: Unpublished artwork detail returns 404

- **WHEN** a client requests an artwork by id/slug whose status is not `published`
- **THEN** the API returns HTTP 404 (indistinguishable from a non-existent id)

#### Scenario: Home feed orders featured before recent

- **WHEN** a client requests the home feed
- **THEN** featured published works are returned before the most recent published works

#### Scenario: Artist detail hides unpublished works

- **WHEN** a client requests a published artist's detail
- **THEN** only that artist's published works are included; unpublished works are omitted

#### Scenario: Unpublished artist profile returns 404

- **WHEN** a client requests an artist profile that is not published
- **THEN** the API returns HTTP 404

### Requirement: Gallery filtering, sorting, and pagination

The gallery list endpoint SHALL support filtering by tag, sorting, and page-number pagination.

#### Scenario: Filter by tags (AND-combined)

- **WHEN** a client requests the gallery with one or more `tag` query parameters
- **THEN** only published works carrying all requested tags are returned

#### Scenario: Sort options

- **WHEN** a client passes `sort=recent`, `sort=price_asc`, or `sort=price_desc`
- **THEN** results are ordered by year descending, price ascending, or price descending respectively (works without a price sort last)

#### Scenario: Paginated results

- **WHEN** a client requests a page of the gallery
- **THEN** the response includes the page of items plus total count and page metadata sufficient to render a pager

### Requirement: Browse-by-location grouping

The API SHALL provide an endpoint returning published works grouped by the region of their owning artist, including a per-region count, omitting regions with no published works.

#### Scenario: Regions with works only

- **WHEN** a client requests works grouped by location
- **THEN** each returned region has at least one published work and reports its count

### Requirement: Authentication and artist signup

The API SHALL support session and token authentication and SHALL allow self-service artist signup. Signup SHALL create an `auth.User` placed in the `Artist` group with a linked `Artist` profile that is not publicly visible until curated.

#### Scenario: Artist signs up

- **WHEN** a visitor POSTs name, email, and password to the signup endpoint with valid data
- **THEN** a user + linked unpublished `Artist` profile is created in the `Artist` group and an auth token is returned

#### Scenario: Login returns a token

- **WHEN** a registered user POSTs valid credentials to the login endpoint
- **THEN** the API returns an auth token usable as a bearer credential on subsequent requests

#### Scenario: Current user endpoint

- **WHEN** an authenticated client requests the current-user endpoint
- **THEN** the API returns the user's identity, role (artist vs curator/admin), and linked artist profile if any

#### Scenario: Duplicate email rejected

- **WHEN** a visitor signs up with an email already in use
- **THEN** the API returns HTTP 400 with a field error

### Requirement: Owner-scoped dashboard endpoints

The API SHALL provide authenticated endpoints for an artist to manage their own content: read/update their profile, CRUD their artworks, upload/reorder/set-primary images, submit content for review, and read inquiries for their own works. An artist SHALL NOT be able to read or modify another artist's content, nor self-publish or self-feature.

#### Scenario: Artist edits own artwork

- **WHEN** an authenticated artist updates an artwork they own
- **THEN** the change is saved and returned

#### Scenario: Artist cannot edit others' artwork

- **WHEN** an authenticated artist attempts to modify an artwork owned by another artist
- **THEN** the API returns HTTP 403 (or 404)

#### Scenario: Artist submits for review

- **WHEN** an artist submits a `draft` artwork they own
- **THEN** its status becomes `submitted` and it appears in the curator review queue

#### Scenario: Artist cannot self-publish or self-feature

- **WHEN** an artist attempts to set status to `published` or set `featured`
- **THEN** the API rejects the request (403) and the status/feature is unchanged

#### Scenario: Artist inbox is scoped

- **WHEN** an artist requests their inquiries inbox
- **THEN** only inquiries about that artist's own works are returned

### Requirement: Image upload, ordering, and primary selection

The API SHALL accept image uploads for an owned artwork, store them as ordered `ArtworkImage` records with a generated thumbnail, allow reordering, and allow designating exactly one primary image (defaulting to the first uploaded).

#### Scenario: Upload sets first image as primary

- **WHEN** an artist uploads the first image for an artwork
- **THEN** that image is stored with a thumbnail and marked primary

#### Scenario: Change primary image

- **WHEN** an artist designates a different image as primary
- **THEN** that image becomes primary and the previous primary is no longer primary

#### Scenario: Non-image upload rejected

- **WHEN** an artist uploads a file that is not a valid image
- **THEN** the API returns HTTP 400 and stores nothing

### Requirement: Curator-only curation endpoints

The API SHALL provide endpoints, restricted to users in the `Curator` group (or admins), to list the review queue and to approve, reject-with-notes, and feature submitted content. Reject SHALL require notes. Feature SHALL only apply to published works.

#### Scenario: Curator approves submission

- **WHEN** a curator approves a `submitted` artwork
- **THEN** its status becomes `published` and it becomes publicly visible

#### Scenario: Reject requires notes

- **WHEN** a curator rejects a submission without providing notes
- **THEN** the API returns HTTP 400 and the status remains `submitted`

#### Scenario: Reject with notes

- **WHEN** a curator rejects a `submitted` artwork with notes
- **THEN** its status becomes `rejected` and the notes are recorded with reviewer and timestamp

#### Scenario: Feature requires published

- **WHEN** a curator attempts to feature an artwork that is not `published`
- **THEN** the API returns HTTP 400

#### Scenario: Non-curator blocked from curation

- **WHEN** an artist (non-curator) calls a curation endpoint
- **THEN** the API returns HTTP 403

#### Scenario: Curator sees all inquiries

- **WHEN** a curator requests the inquiries inbox
- **THEN** inquiries across all artworks are returned

### Requirement: Inquiry submission

The API SHALL allow an unauthenticated visitor to submit an inquiry against a published artwork with name, email, and message, validating the email, and SHALL record the inquiry against the artwork and its artist. No cart, checkout, order, or payment endpoint SHALL exist.

#### Scenario: Valid inquiry recorded

- **WHEN** a visitor POSTs a valid name, email, and message for a published artwork
- **THEN** the inquiry is stored against that artwork/artist and a confirmation (HTTP 201) is returned

#### Scenario: Invalid email rejected

- **WHEN** a visitor submits an inquiry with a malformed email
- **THEN** the API returns HTTP 400 with a field error and stores nothing

#### Scenario: Inquiry on unpublished artwork rejected

- **WHEN** a visitor submits an inquiry referencing an artwork that is not published
- **THEN** the API returns HTTP 404 and stores nothing

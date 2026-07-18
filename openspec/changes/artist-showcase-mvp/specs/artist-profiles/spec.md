## ADDED Requirements

### Requirement: Artist Entity and Profile Fields
The system SHALL provide an `Artist` entity with a unique URL `slug`, a `display_name`, an optional `bio`/`statement`, an optional `avatar` image, optional external `links` (e.g. website, social), and contact routing for inquiries. The `slug` SHALL be unique and used to build the public profile URL.

#### Scenario: Artist created with required fields
- **WHEN** a curator creates an artist with a `display_name`
- **THEN** the system generates a unique `slug` from the name
- **AND** the artist record is persisted with empty optional fields allowed.

#### Scenario: Duplicate slug is disambiguated
- **WHEN** a second artist is created whose name produces an already-used `slug`
- **THEN** the system generates a distinct `slug` (e.g. by appending a suffix)
- **AND** both artists remain individually addressable by URL.

### Requirement: Artist–User Account Linkage
The system SHALL link each `Artist` profile one-to-one with a Django `auth.User`. Users in the `Artist` group SHALL be able to manage only the `Artist` profile linked to them.

#### Scenario: Linked user manages own profile
- **WHEN** an authenticated user linked to an artist opens their profile in the dashboard
- **THEN** the system grants edit access to that artist profile only.

#### Scenario: User cannot access another artist's profile
- **WHEN** an authenticated artist requests the dashboard edit page of a different artist
- **THEN** the system denies access with a 403/redirect
- **AND** no profile data of the other artist is exposed.

### Requirement: Artist Location
The system SHALL store an artist `city` and `region` as text, and MAY store an optional geographic point (PostGIS) for future mapping. Location SHALL be optional and SHALL NOT block profile creation.

#### Scenario: Profile saved without location
- **WHEN** an artist profile is saved with no city or region
- **THEN** the profile is valid and persisted
- **AND** the artist is excluded from location-filtered browsing until a region is set.

#### Scenario: Region powers location browsing
- **WHEN** an artist has `region = "Jalisco"` and at least one published artwork
- **THEN** that artwork appears under the "Jalisco" group in the browse-by-location section.

### Requirement: Public Profile Visibility Gating
The public artist profile page SHALL be reachable only when the artist profile is published, and it SHALL list only that artist's published artworks.

#### Scenario: Unpublished artist profile is not public
- **WHEN** a visitor requests the public URL of an artist whose profile is not published
- **THEN** the system returns 404 (the profile is not publicly listed).

#### Scenario: Published profile hides unpublished works
- **WHEN** a visitor views a published artist's profile that has both published and draft artworks
- **THEN** only the published artworks are shown.

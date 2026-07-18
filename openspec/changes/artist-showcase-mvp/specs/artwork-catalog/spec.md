## ADDED Requirements

### Requirement: Artwork Entity and Ownership
The system SHALL provide an `Artwork` entity owned by exactly one `Artist` (foreign key). An artwork SHALL have a `title`, an optional `description`, an optional `medium`, optional `dimensions`, an optional `year`, and a unique-per-artist URL `slug`. Deleting an artist SHALL cascade to that artist's artworks.

#### Scenario: Artwork belongs to its artist
- **WHEN** an artwork is created under an artist
- **THEN** the artwork is retrievable from that artist's artwork set
- **AND** the artwork's public URL is namespaced under the artist.

#### Scenario: Artwork requires a title
- **WHEN** an artwork is saved without a title
- **THEN** the system rejects it with a validation error.

### Requirement: Artwork Images
The system SHALL allow one or more images per artwork via an `ArtworkImage` relation, each with a `position` for ordering and an `is_primary` flag. Exactly one image SHALL be the primary image; if none is explicitly marked, the first by `position` SHALL be treated as primary. Uploaded images SHALL be validated as images and a thumbnail SHALL be generated.

#### Scenario: First uploaded image becomes primary
- **WHEN** an artist uploads the first image for an artwork without marking a primary
- **THEN** that image is treated as the primary image used in listings.

#### Scenario: Changing the primary image
- **WHEN** an artist marks a different image as primary
- **THEN** the previously primary image is no longer primary
- **AND** listings use the newly primary image.

#### Scenario: Non-image upload rejected
- **WHEN** a file that is not a valid image is uploaded as an artwork image
- **THEN** the system rejects the upload with a validation error.

### Requirement: Price and Availability
The system SHALL store an optional `price` (decimal) with a `currency` (single configurable default for MVP) and an `availability` status of `available`, `sold`, or `not_for_sale`. Price SHALL be optional; availability SHALL default to `available`.

#### Scenario: Artwork without a price
- **WHEN** an artwork has no price set
- **THEN** the detail page omits a price figure
- **AND** the Inquire action is still offered.

#### Scenario: Sold artwork is labelled
- **WHEN** an artwork's availability is `sold`
- **THEN** the detail and listing views display a "Sold" label
- **AND** the artwork remains visible if published.

### Requirement: Tags
The system SHALL allow zero or more free-form tags per artwork to support grouping and discovery.

#### Scenario: Tagged artwork is grouped
- **WHEN** a published artwork is tagged `"painting"`
- **THEN** it appears when browsing the `"painting"` tag.

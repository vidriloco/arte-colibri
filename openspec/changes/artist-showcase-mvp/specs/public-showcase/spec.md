## ADDED Requirements

### Requirement: Home Page Identity
The home page at `/` SHALL communicate, within the first viewport, that the site is a curated showcase of artwork by local artists. It SHALL present a hero conveying that identity and a grid of curated works drawn from `featured` artworks first, then recent `published` artworks. It SHALL replace the existing placeholder landing page.

#### Scenario: Identity is immediately clear
- **WHEN** a first-time visitor loads `/`
- **THEN** the hero copy conveys "curated artwork by local artists"
- **AND** a grid of published/featured artworks is visible without scrolling past the first screen on a typical desktop viewport.

#### Scenario: Featured works lead the grid
- **WHEN** there is at least one featured published artwork
- **THEN** featured artworks appear before non-featured published artworks in the home grid.

#### Scenario: Empty state
- **WHEN** there are no published artworks
- **THEN** the home page still renders the identity hero with a graceful empty state instead of an error.

### Requirement: Gallery Browse
The system SHALL provide a gallery page listing `published` artworks with their primary image, title, artist, and price/availability, with pagination. The gallery SHALL support filtering by tag.

#### Scenario: Gallery lists published works
- **WHEN** a visitor opens the gallery
- **THEN** only published artworks are listed, each linking to its detail page.

#### Scenario: Filter by tag
- **WHEN** a visitor filters the gallery by a tag
- **THEN** only published artworks carrying that tag are shown.

### Requirement: Artwork Detail Page
The system SHALL provide an artwork detail page showing the artwork's images, title, artist (linking to the artist profile), medium/dimensions/year when present, description, price when set, availability label, and an **Inquire** action. No cart, checkout, or payment SHALL be offered.

#### Scenario: Detail shows price and inquire
- **WHEN** a visitor opens a published artwork that has a price
- **THEN** the page shows the price and an Inquire action
- **AND** no add-to-cart or checkout control is present.

#### Scenario: Detail for unpublished artwork is blocked
- **WHEN** a visitor requests the detail URL of a non-published artwork
- **THEN** the system returns 404.

### Requirement: Artist Profile Page
The system SHALL provide a public artist profile page showing the artist's name, bio/statement, location, links, and a grid of that artist's `published` artworks. It SHALL be reachable only for published artist profiles.

#### Scenario: Profile lists the artist's published works
- **WHEN** a visitor opens a published artist's profile
- **THEN** the page shows the artist details and a grid of their published artworks only.

### Requirement: Browse by Location
The system SHALL provide a secondary "browse by location" section that groups `published` artworks by their artist's region. This section SHALL be secondary to the main showcase (not the primary navigation emphasis).

#### Scenario: Location section groups by region
- **WHEN** a visitor opens the browse-by-location section
- **THEN** published artworks are grouped by their artist's region
- **AND** artists without a region are excluded from the grouping.

### Requirement: Inquiry Submission
The system SHALL allow a visitor to submit an inquiry about a specific published artwork, capturing the visitor's name, email, and message. Submitting an inquiry SHALL record it for the owning artist/curator and SHALL NOT initiate any payment.

#### Scenario: Visitor submits an inquiry
- **WHEN** a visitor submits the inquiry form on a published artwork with a valid name, email, and message
- **THEN** the inquiry is recorded against that artwork and its artist
- **AND** the visitor sees a confirmation.

#### Scenario: Invalid inquiry is rejected
- **WHEN** a visitor submits the inquiry form with a missing or malformed email
- **THEN** the system rejects it with a validation error and no inquiry is recorded.

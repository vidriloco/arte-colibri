## ADDED Requirements

### Requirement: Home identity and showcase carousel hero

The home screen SHALL communicate "curated artwork by local artists" within the first viewport. It SHALL open with a full-bleed **showcase carousel hero** featuring the 5 most recent published works as a cross-fading background behind the brand identity (name, eyebrow, tagline), with a caption naming the current work + artist, a counter, previous/next controls, keyboard arrow navigation, auto-advance with pause-on-hover, and numbered progress ticks. Below the hero it SHALL show featured-first then recent published works and a secondary browse-by-location teaser.

#### Scenario: Hero shows recent works

- **WHEN** the home screen loads with published works available
- **THEN** the carousel hero cycles the 5 most recent published works with the brand name and tagline overlaid

#### Scenario: Carousel navigation

- **WHEN** the user presses the arrow keys or clicks the next/previous controls
- **THEN** the hero advances to the corresponding work and its caption updates

#### Scenario: Auto-advance pauses on hover

- **WHEN** the pointer is over the carousel
- **THEN** auto-advance pauses, and resumes when the pointer leaves

#### Scenario: Featured before recent

- **WHEN** the home grid renders
- **THEN** featured published works appear before the recent published works

#### Scenario: Empty home state

- **WHEN** there are no published works
- **THEN** the home screen still shows the identity hero and a graceful empty message, not an error

### Requirement: Gallery with filtering, sorting, and pagination

The gallery screen SHALL list published artworks as cards (primary image, title, artist, price/availability) and SHALL provide tag filter chips, a sort control (recent / price low-to-high / price high-to-low), and pagination. Card price area SHALL show the price when set or the availability label otherwise.

#### Scenario: Filter by tag

- **WHEN** the user activates one or more tag chips
- **THEN** the grid shows only published works matching all selected tags and pagination resets to page one

#### Scenario: Sort works

- **WHEN** the user selects a sort option
- **THEN** the grid reorders accordingly (recent, price ascending, or price descending)

#### Scenario: Paginate

- **WHEN** there are more works than one page
- **THEN** a pager is shown and selecting a page updates the visible works

#### Scenario: No results for filter combination

- **WHEN** a filter combination yields no works
- **THEN** an empty "no results" state with a clear-filters action is shown

### Requirement: Artwork detail with inquire (no checkout)

The artwork detail screen SHALL show a large primary image with a thumbnail strip for additional images, title, artist name linking to the profile, medium/dimensions/year, description, price (when set) with an availability label (Available / Sold / Not for sale), and a prominent **Inquire** action. There SHALL be no add-to-cart or checkout anywhere. Inquire SHALL open a modal collecting name, email, and message with validation and a success confirmation.

#### Scenario: Switch primary image

- **WHEN** the user selects a thumbnail
- **THEN** the large image updates to the selected image

#### Scenario: Availability label shown

- **WHEN** the artwork is sold or not-for-sale
- **THEN** the corresponding label is displayed and the inquire action reflects availability (e.g. disabled for sold)

#### Scenario: Inquiry validation error

- **WHEN** the user submits the inquiry with a missing or invalid field
- **THEN** inline validation errors are shown and nothing is submitted

#### Scenario: Inquiry success

- **WHEN** the user submits a valid inquiry
- **THEN** the modal shows a success confirmation and the inquiry is sent to the API

#### Scenario: Unpublished or missing artwork

- **WHEN** the user opens a detail URL for an artwork that is not published or does not exist
- **THEN** the screen shows the 404 / unavailable state with a path back to the gallery

### Requirement: Artist profile and artists listing

The SPA SHALL provide an artist profile screen (avatar/initials, name, discipline, location, bio/statement, external links, and a grid of that artist's published works) and an artists listing screen showing all artists with published work, navigable to each profile.

#### Scenario: Artist profile lists own works

- **WHEN** a user opens a published artist's profile
- **THEN** the artist's identity, statement, links, and a grid of their published works are shown

#### Scenario: Navigate from artwork to artist

- **WHEN** a user clicks the artist name on an artwork detail
- **THEN** the SPA navigates to that artist's profile

#### Scenario: Unpublished artist profile

- **WHEN** a user opens a profile that is not published
- **THEN** the 404 / unavailable state is shown

### Requirement: Browse by location

The SPA SHALL provide a secondary browse-by-location screen that groups published works by the region of their artist, showing per-region counts, and a home teaser linking into it. Location SHALL be a secondary entry point, not the headline.

#### Scenario: Works grouped by region

- **WHEN** a user opens browse-by-location
- **THEN** published works are grouped under their artist's region with a count per region, omitting empty regions

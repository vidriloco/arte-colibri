## ADDED Requirements

### Requirement: Authenticated Access and Roles
The dashboard SHALL be served under `/dashboard` and SHALL require authentication. Access SHALL be role-based: users in the `Artist` group manage only their own profile and artworks; users in the `Curator` group (and admins) manage all content and perform curation actions. Anonymous users SHALL be redirected to login.

#### Scenario: Anonymous user redirected to login
- **WHEN** an anonymous visitor opens any `/dashboard` URL
- **THEN** the system redirects them to the login page.

#### Scenario: Artist sees only their content
- **WHEN** an artist opens the dashboard
- **THEN** the dashboard lists only that artist's profile and artworks
- **AND** no other artist's content is listed.

#### Scenario: Curator sees all content
- **WHEN** a curator opens the dashboard
- **THEN** the dashboard provides access to all artists, all artworks, the review queue, and inquiries.

### Requirement: Artist Manages Own Profile
The dashboard SHALL let an artist edit their own profile fields (display name, bio/statement, avatar, links, location) and submit the profile for review.

#### Scenario: Artist edits profile
- **WHEN** an artist saves changes to their own profile
- **THEN** the changes are persisted
- **AND** if the profile was published, the change does not bypass curation rules configured for profiles.

### Requirement: Artist Manages Own Artworks
The dashboard SHALL let an artist create, edit, and delete their own artworks, upload and order images, set price/availability/tags, and submit drafts for review. An artist SHALL NOT be able to set the `published` or `featured` flags directly.

#### Scenario: Artist creates and submits an artwork
- **WHEN** an artist creates an artwork, adds an image, and submits it
- **THEN** the artwork is saved as `draft` then transitions to `submitted`
- **AND** it appears in the curator review queue.

#### Scenario: Artist cannot self-publish
- **WHEN** an artist attempts to set their artwork's status to `published` directly
- **THEN** the action is denied
- **AND** publishing remains a curator-only action.

### Requirement: Curator Review Queue and Actions
The dashboard SHALL present curators a queue of `submitted` artworks and profiles, and SHALL provide approve, reject-with-notes, and feature actions consistent with the curation workflow.

#### Scenario: Curator approves from the queue
- **WHEN** a curator approves a submitted artwork from the review queue
- **THEN** the artwork becomes `published`
- **AND** it is removed from the submitted queue.

#### Scenario: Curator rejects with notes
- **WHEN** a curator rejects a submitted artwork and provides notes
- **THEN** the artwork becomes `rejected` with the notes recorded
- **AND** it leaves the submitted queue.

### Requirement: Inquiries Inbox
The dashboard SHALL show inquiries: artists see inquiries about their own artworks; curators/admins see all inquiries. Each inquiry SHALL show the artwork, visitor name, email, message, and timestamp.

#### Scenario: Artist sees inquiries for own work
- **WHEN** an artist opens the inquiries inbox
- **THEN** only inquiries about that artist's artworks are listed.

#### Scenario: Curator sees all inquiries
- **WHEN** a curator opens the inquiries inbox
- **THEN** inquiries across all artworks are listed.

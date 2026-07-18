## ADDED Requirements

### Requirement: Moderation States
The system SHALL track a moderation `status` on each artwork (and artist profile) with the values `draft`, `submitted`, `published`, and `rejected`. New records SHALL start as `draft`. The system SHALL record `reviewed_by`, `reviewed_at`, and `review_notes` when a curator acts.

#### Scenario: New artwork starts as draft
- **WHEN** an artist creates a new artwork
- **THEN** its status is `draft`
- **AND** it is not publicly visible.

#### Scenario: Review metadata captured on decision
- **WHEN** a curator approves or rejects a submitted artwork
- **THEN** `reviewed_by` is set to the curator and `reviewed_at` to the decision time.

### Requirement: Submission for Review
The system SHALL allow an artist to submit their own `draft` artwork (or profile) for review, transitioning it to `submitted`. Only the owning artist (or a curator/admin) SHALL be able to submit a record.

#### Scenario: Artist submits a draft
- **WHEN** an artist submits their `draft` artwork
- **THEN** its status becomes `submitted`
- **AND** it appears in the curator review queue.

#### Scenario: Non-owner cannot submit
- **WHEN** an artist attempts to submit another artist's draft
- **THEN** the action is denied and the status is unchanged.

### Requirement: Curator Review Actions
The system SHALL allow users in the `Curator` (or admin) role to approve or reject `submitted` records. Approving SHALL set status to `published`; rejecting SHALL set status to `rejected` and SHALL require `review_notes`.

#### Scenario: Approve publishes the artwork
- **WHEN** a curator approves a `submitted` artwork
- **THEN** its status becomes `published`
- **AND** it becomes publicly visible.

#### Scenario: Reject requires a reason
- **WHEN** a curator rejects a `submitted` artwork without providing review notes
- **THEN** the system rejects the action with a validation error.

#### Scenario: Rejected item returns to the artist
- **WHEN** a curator rejects an artwork with notes
- **THEN** its status becomes `rejected`
- **AND** the owning artist can see the notes and resubmit after edits.

### Requirement: Public Visibility Gating
The system SHALL expose only `published` content to the public, enforced at the query layer via a `published` manager/queryset used by all public views. Non-published content SHALL NOT be reachable through any public URL.

#### Scenario: Only published artworks are queryable publicly
- **WHEN** any public showcase view lists artworks
- **THEN** the query returns only artworks whose status is `published`.

#### Scenario: Direct access to unpublished artwork is blocked
- **WHEN** a visitor requests the public URL of a `draft`, `submitted`, or `rejected` artwork
- **THEN** the system returns 404.

### Requirement: Featuring
The system SHALL allow curators to mark a `published` artwork as `featured`. Featured artworks SHALL be eligible for prominent placement (e.g. the home page). Only curators/admins SHALL set the featured flag.

#### Scenario: Curator features a published artwork
- **WHEN** a curator marks a `published` artwork as featured
- **THEN** it becomes eligible for the home page featured grid.

#### Scenario: Featuring requires published status
- **WHEN** a curator attempts to feature a non-`published` artwork
- **THEN** the action is denied.

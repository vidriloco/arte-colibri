## ADDED Requirements

### Requirement: Artist application / signup flow

The SPA SHALL provide an open-call artist application flow reachable from the nav and footer. It SHALL collect account creation (name, email, password + confirmation, terms acceptance) with validation, then present an onboarding dashboard with two tasks — "complete your profile" and "upload your first artwork" — and a submit action that is enabled only when both tasks are complete. On submit it SHALL show a success state ("received · we'll contact you within five business days") with options to submit another work or return home.

#### Scenario: Account validation

- **WHEN** the applicant submits the account step with a missing field, invalid email, too-short password, mismatched confirmation, or unaccepted terms
- **THEN** inline errors are shown and the flow does not advance

#### Scenario: Onboarding tasks gate submission

- **WHEN** the applicant has completed neither or only one of the profile/artwork tasks
- **THEN** the final submit action is disabled with a hint to complete both steps

#### Scenario: Completed task is marked done

- **WHEN** the applicant finishes the profile or artwork task and returns to the onboarding dashboard
- **THEN** that task shows a completed state and progress advances

#### Scenario: Submission success

- **WHEN** both tasks are complete and the applicant submits
- **THEN** the account + artist profile + first artwork are created via the API and a success confirmation is shown

### Requirement: Artist dashboard — own content management

The authenticated artist dashboard SHALL list the artist's own artworks with a status badge (Draft / Submitted / Published / Rejected), and SHALL let the artist create and edit artworks (images with ordering and a primary, medium, dimensions, year, price or not-for-sale, tags, bilingual title/description), submit a draft for review, and edit their own profile. The artist SHALL NOT be able to publish or feature their own work.

#### Scenario: Status badges reflect state

- **WHEN** the artist views their artwork list
- **THEN** each artwork shows a badge matching its moderation status

#### Scenario: Create and edit artwork

- **WHEN** the artist creates or edits an owned artwork and saves
- **THEN** the change is persisted via the API and reflected in the list

#### Scenario: Image upload and ordering

- **WHEN** the artist uploads multiple images and reorders them / sets a primary
- **THEN** the order and primary selection are saved, with the first upload defaulting to primary

#### Scenario: Submit for review

- **WHEN** the artist submits a draft artwork
- **THEN** its status changes to Submitted and it leaves the editable-draft state

#### Scenario: No self-publish or self-feature

- **WHEN** the artist views their own artwork controls
- **THEN** there is no control to set Published or Featured, and attempting it is rejected by the API

### Requirement: Curator dashboard — review and curation

The authenticated curator dashboard SHALL present a review queue of submitted artworks and profiles with actions to approve, reject-with-notes (notes required), and feature (published works only), and SHALL provide access to all content and all inquiries.

#### Scenario: Approve a submission

- **WHEN** a curator approves a submitted artwork
- **THEN** it becomes published and disappears from the review queue

#### Scenario: Reject requires notes

- **WHEN** a curator attempts to reject without notes
- **THEN** the action is blocked and a notes-required validation message is shown

#### Scenario: Feature a published work

- **WHEN** a curator features a published work
- **THEN** it is marked featured and surfaces in the featured-first home ordering

#### Scenario: Curator sees all inquiries

- **WHEN** a curator opens the inquiries inbox
- **THEN** inquiries across all artworks are listed

### Requirement: Inquiries inbox

The dashboard SHALL provide an inquiries inbox showing visitor inquiries (artwork, name, email, message, date). Artists SHALL see only inquiries about their own works; curators SHALL see all inquiries.

#### Scenario: Artist inbox scoped to own works

- **WHEN** an artist opens their inquiries inbox
- **THEN** only inquiries about that artist's works are shown

#### Scenario: Inbox shows inquiry details

- **WHEN** an inquiry exists for a work
- **THEN** the inbox shows the artwork, visitor name, email, message, and date

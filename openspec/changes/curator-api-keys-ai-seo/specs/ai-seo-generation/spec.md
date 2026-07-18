## ADDED Requirements

### Requirement: Generate SEO fields from a page description

The system SHALL provide a curator-only action that, for a given page SEO slot, generates a
complete SEO field set from that slot's description using the configured `openrouter` API key.
The generated set SHALL cover meta title and description, Open Graph title and description,
keywords, and image alt text, each in both Spanish and English. The action SHALL read the
slot's Spanish description as the source when present, otherwise the English description.

#### Scenario: Curator generates SEO for a slot

- **WHEN** a curator triggers generation for a slot that has a description and an `openrouter`
  key is configured
- **THEN** the response contains title, description, OG title, OG description, keywords, and
  image alt, each as a `{ "es": …, "en": … }` pair

#### Scenario: Source language follows the available description

- **WHEN** a slot has only an English description
- **THEN** generation uses the English text as the source and still returns both ES and EN fields

### Requirement: Generation is a reviewable draft, not an automatic save

The system SHALL return generated values for the curator to review and SHALL NOT persist them
as part of the generation request. The values become the slot's SEO only when the curator
saves them through the existing update endpoint.

#### Scenario: Generated values are not auto-saved

- **WHEN** generation returns a set of fields
- **THEN** the stored slot is unchanged until the curator explicitly saves
- **AND** the curator can edit the generated values before saving

### Requirement: Generation is gated on a configured key

The system SHALL only offer and perform generation when an `openrouter` key is configured. When
no key is set, the action SHALL be rejected with a clear error and the client SHALL NOT display
the generate affordance.

#### Scenario: No key configured

- **WHEN** a curator triggers generation with no `openrouter` key stored
- **THEN** the request is rejected with a clear "no OpenRouter key configured" error
- **AND** nothing is sent to the provider

#### Scenario: Generate affordance hidden without a key

- **WHEN** the SEO editor loads and no `openrouter` key is configured
- **THEN** the Generate control is not shown

### Requirement: Safe handling of missing description and provider failures

The system SHALL reject generation with a clear error when the slot has neither a Spanish nor
an English description. When the provider call fails or returns an unusable response, the system
SHALL surface a clear error and SHALL NOT persist or partially apply any values. The secret key
SHALL be sent only from the server to the provider and never exposed to the browser.

#### Scenario: Empty description

- **WHEN** a curator triggers generation for a slot whose Spanish and English descriptions are
  both blank
- **THEN** the request is rejected with a message to add a description first

#### Scenario: Provider error

- **WHEN** the provider call errors or returns an unparseable result
- **THEN** the curator sees a clear failure message and the slot is left unchanged

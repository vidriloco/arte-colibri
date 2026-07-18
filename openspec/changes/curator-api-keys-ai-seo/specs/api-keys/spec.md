## ADDED Requirements

### Requirement: Curator-managed API key store

The system SHALL persist third-party API keys as records keyed by an **API type** (an
enumerated value, initially `openrouter`) holding a secret **key value**. There SHALL be at
most one stored key per API type; saving a key for a type that already exists SHALL replace
it. Only users in the `Curator` group (or admins) SHALL create, read, update, or delete these
records; artists and anonymous visitors SHALL be rejected with 403 (or 401 if unauthenticated).

#### Scenario: Curator stores an OpenRouter key

- **WHEN** a curator submits a key value for the `openrouter` type
- **THEN** the key is stored and reported as configured for that type

#### Scenario: Re-saving a type replaces the key

- **WHEN** a curator saves a new value for a type that already has a key
- **THEN** the stored value is replaced and no duplicate record is created

#### Scenario: Non-curator cannot manage keys

- **WHEN** an artist or anonymous client calls the API-keys endpoints
- **THEN** the request is rejected with 403 (or 401 if unauthenticated)

### Requirement: Secret values are never returned to a client

The system SHALL treat the key value as write-only: it SHALL accept it on create/update but
SHALL NOT include the raw secret in any API response. Reads SHALL expose only the API type,
whether a key is set, a masked preview (last few characters), and when it was updated.

#### Scenario: Listing keys hides the secret

- **WHEN** a curator lists the stored API keys
- **THEN** each entry shows its type, a "configured" flag, and a masked preview
- **AND** the full secret value does not appear in the response

#### Scenario: Saving a key does not echo it back

- **WHEN** a curator saves a key value
- **THEN** the response confirms it is set without returning the raw value

### Requirement: Deleting a key

The system SHALL let a curator delete the stored key for a type, after which that type is
reported as not configured and any feature gated on it becomes unavailable.

#### Scenario: Curator removes a key

- **WHEN** a curator deletes the `openrouter` key
- **THEN** the type is reported as not configured
- **AND** the SEO generation action gated on it is no longer offered

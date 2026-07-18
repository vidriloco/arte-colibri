## ADDED Requirements

### Requirement: Artist images stored on AWS S3

The system SHALL store all artist-uploaded images — artwork images, their generated
thumbnails, and artist profile avatars — as objects in the configured AWS S3 bucket, and
SHALL persist each object's **public URL** on the corresponding database record. New
uploads SHALL NOT be written to the local `MEDIA_ROOT` filesystem. Object keys SHALL be
derived deterministically from stable identifiers (artist/artwork slug and record id) so
the same logical image always maps to the same key.

#### Scenario: Uploaded artwork image lands in S3

- **WHEN** an artist uploads a valid artwork image
- **THEN** the image bytes are stored as an S3 object under the artwork's key namespace
- **AND** the record's public S3 URL is persisted and returned in the API response
- **AND** no file is written under the local media directory.

#### Scenario: Uploaded avatar lands in S3

- **WHEN** an artist uploads a valid profile avatar
- **THEN** the avatar bytes are stored as an S3 object under the artist's avatar key
- **AND** the artist record's persisted avatar URL is the object's public S3 URL.

#### Scenario: S3 not configured fails loudly

- **WHEN** an image upload is attempted while AWS credentials/bucket are not configured
- **THEN** the request fails with a server error surfaced to the client
- **AND** no image is written to the local filesystem as a silent fallback.

### Requirement: Profile avatar size limit of 200 KB

The system SHALL reject an artist profile avatar upload whose file size exceeds
**200 kilobytes (204800 bytes)**. The size check SHALL be performed on the uploaded file
before any object is written to S3, and the rejection SHALL be an HTTP 400 with a
validation error identifying the size limit.

#### Scenario: Avatar within the limit is accepted

- **WHEN** an artist uploads an avatar of 200 KB or less that is a valid image
- **THEN** the upload succeeds and the avatar URL is persisted.

#### Scenario: Oversized avatar is rejected

- **WHEN** an artist uploads an avatar larger than 200 KB
- **THEN** the request is rejected with HTTP 400 and an error stating the 200 KB limit
- **AND** no object is written to S3 and the artist's existing avatar is unchanged.

### Requirement: Artwork image size limit of 500 KB

The system SHALL reject an artwork image upload whose file size exceeds
**500 kilobytes (512000 bytes)**. The size check SHALL be performed on the uploaded file
before any object is written to S3, and the rejection SHALL be an HTTP 400 with a
validation error identifying the size limit.

#### Scenario: Artwork image within the limit is accepted

- **WHEN** an artist uploads an artwork image of 500 KB or less that is a valid image
- **THEN** the upload succeeds and the image (and its thumbnail) URLs are persisted.

#### Scenario: Oversized artwork image is rejected

- **WHEN** an artist uploads an artwork image larger than 500 KB
- **THEN** the request is rejected with HTTP 400 and an error stating the 500 KB limit
- **AND** no object is written to S3.

### Requirement: Uploads must be valid images

The system SHALL validate that every uploaded file is a decodable image before storing it,
independent of the size limit. Files that are not valid images SHALL be rejected with an
HTTP 400 validation error, and SHALL NOT be uploaded to S3.

#### Scenario: Non-image upload rejected

- **WHEN** a file that is not a valid image is uploaded as an artwork image or avatar
- **THEN** the request is rejected with HTTP 400 and a validation error
- **AND** no object is written to S3.

### Requirement: Artwork image upload endpoint

The system SHALL expose an authenticated endpoint for the owning artist to upload an image
to one of their artworks. On success the endpoint SHALL create an `ArtworkImage`, generate
a thumbnail, store both the original and the thumbnail on S3, persist their public URLs,
and return the serialized image. The first image uploaded to an artwork SHALL become its
primary image when none is marked. Only the owner of the artwork (or an admin/curator)
SHALL be permitted to upload; other callers SHALL be rejected with 403 (or 401 if
unauthenticated).

#### Scenario: Owner uploads an artwork image

- **WHEN** the owning artist POSTs a valid image (≤ 500 KB) to their artwork's image endpoint
- **THEN** an `ArtworkImage` is created with the original and thumbnail S3 URLs
- **AND** the response is HTTP 201 with the serialized image.

#### Scenario: First image becomes primary

- **WHEN** an artist uploads the first image for an artwork without marking a primary
- **THEN** that image is stored as the artwork's primary image.

#### Scenario: Non-owner cannot upload

- **WHEN** a client who does not own the artwork attempts to upload an image to it
- **THEN** the request is rejected with 403 (or 401 if unauthenticated)
- **AND** no object is written to S3.

### Requirement: Artist avatar upload endpoint

The system SHALL expose an authenticated endpoint for an artist to upload or replace their
profile avatar. On success the endpoint SHALL store the avatar on S3, persist its public
URL on the artist record, and return the updated artist. Only the owner of the artist
profile (or an admin/curator) SHALL be permitted to upload; other callers SHALL be
rejected with 403 (or 401 if unauthenticated). Replacing an existing avatar SHALL update
the persisted URL to the new object.

#### Scenario: Artist replaces their avatar

- **WHEN** an artist uploads a new valid avatar (≤ 200 KB) to their avatar endpoint
- **THEN** the avatar is stored on S3 and the artist's persisted avatar URL is updated
- **AND** the response returns the updated artist with the new avatar URL.

#### Scenario: Non-owner cannot change an avatar

- **WHEN** a client attempts to set the avatar of an artist profile they do not own
- **THEN** the request is rejected with 403 (or 401 if unauthenticated).

### Requirement: Deleting an image removes its S3 objects

The system SHALL expose an authenticated endpoint for the owning artist to delete one of
their artwork images, and deleting the image SHALL remove both the original and thumbnail
objects from S3 (best-effort) in addition to removing the database record. When the deleted
image was primary, the system SHALL promote the next image (by position) to primary.

#### Scenario: Deleting an artwork image

- **WHEN** the owning artist deletes an artwork image
- **THEN** the image record is removed and its S3 objects are deleted
- **AND** if it was the primary image, the next image by position becomes primary.

#### Scenario: Delete tolerates a missing S3 object

- **WHEN** an image is deleted but its S3 object is already absent
- **THEN** the database record is still removed and the request succeeds.

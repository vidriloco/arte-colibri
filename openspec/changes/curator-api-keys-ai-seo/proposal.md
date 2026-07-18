## Why

Filling every SEO slot by hand — bilingual meta title/description, social title/description,
keywords, and image alt text — is tedious and easy to leave half-done. The curator already
writes a page description; an LLM can turn that into a complete, well-formed SEO set in both
languages in one click. To do that the platform needs a place to hold a third-party API key,
and a generation action that uses it.

## What Changes

- Introduce a curator-managed **API keys** store: a small table keyed by **API type**
  (starting with `openrouter`) holding the **key value**. Keys are entered/updated from a new
  dashboard section and are **never returned in full** by the API (write-only; reads are
  masked to a preview).
- Add an **AI SEO generation** action to the SEO tab: when an `openrouter` key is configured,
  each page slot shows a **Generate** button. It reads that slot's description (Spanish
  preferred, English otherwise), calls **OpenRouter** server-side, and returns a full SEO set
  — meta title/description, OG title/description, keywords, and image alt — **in both ES and
  EN**. The values populate the editor for the curator to review and Save; nothing is
  persisted automatically.
- Add a server-side **OpenRouter client** (`world/utils/openrouter.py`) that sends the prompt
  and parses the model's JSON reply into the SEO field shape.
- New **curator-only endpoints**: manage API keys, and generate SEO for a slot. The
  OpenRouter key is used only server-side and is never exposed to the browser.

## Capabilities

### New Capabilities
- `api-keys`: curator-managed storage of typed third-party API keys (type + secret value),
  their curator-only management endpoints, and the write-only/masked-read handling that keeps
  the secret from ever being returned to a client.
- `ai-seo-generation`: generating a complete bilingual SEO field set for a page slot from its
  description via OpenRouter, gated on an `openrouter` key being configured, returned as a
  reviewable draft rather than auto-saved.

### Modified Capabilities
<!-- None. `page-seo` (from manage-page-seo) is not changed at the requirement level: the same
     fields are simply also fillable via the new generation action. -->

## Impact

- **Code:** new `world/models/api_key.py` (`ApiKey`) + migration; new
  `world/utils/openrouter.py`; `world/api/serializers.py` (masked `ApiKeySerializer`);
  `world/api/views.py` (API-keys CRUD + a `generate` action on `CurationSeoViewSet`);
  `world/api/urls.py`. Frontend: a new **API Keys** dashboard section, a **Generate** button
  in `SeoTab.jsx`, `api.js` methods, and i18n strings.
- **APIs:** `curation/api-keys/…` (list/create/update/delete, masked) and
  `curation/seo/<key>/generate/` (curator-only).
- **Dependencies:** none new — OpenRouter is called over HTTPS with the existing `requests`.
- **Config:** optional `OPENROUTER_MODEL` (env) default for the model id; optional
  `OPENROUTER_BASE_URL`. No key in env — the key lives in the DB per this change.
- **Security:** secrets are stored in the DB (as requested) behind curator auth, write-only
  over the API, masked on read, and sent only from server → OpenRouter. At-rest encryption is
  called out as a follow-up.

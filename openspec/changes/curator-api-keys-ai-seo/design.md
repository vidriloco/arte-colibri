## Context

The SEO tab (`page-seo` capability) lets curators edit, per page slot, a bilingual field set:
meta title/description, OG title/description, `og_image`, image alt, keywords, canonical, and
robots. Everything is entered by hand. Curators already write a page **description**; this
change lets an LLM expand that into the full SEO set in both languages.

The platform has no place to keep third-party API keys. Inburgering keeps provider creds in
env; here the request is explicit: a **DB table** the curator manages, keyed by API type, so
keys can be added without a redeploy. The first (only, for now) consumer is **OpenRouter**,
an OpenAI-compatible chat-completions gateway reachable over plain HTTPS with `requests`.

## Goals / Non-Goals

**Goals:**
- A curator-managed `ApiKey` store (type + secret value), never leaking the secret back to a
  client, manageable from the dashboard.
- A one-click, per-slot **Generate** that turns a slot's description into a complete bilingual
  SEO set via OpenRouter, returned as a **reviewable draft** the curator saves explicitly.
- Read whichever description is present (Spanish preferred, English otherwise) as the source;
  produce **every** SEO field in **both** ES and EN (translating).
- Fail clearly and safely when no key is set, the description is empty, or OpenRouter errors.

**Non-Goals:**
- At-rest encryption / a secrets manager (KMS, Vault). Keys are stored in the DB behind
  curator auth as requested; encryption is a called-out follow-up.
- Auto-saving generated values, or generating for artwork/artist detail pages (those derive
  their meta from content already).
- Supporting other providers now. The type field is an enum so more can be added later.
- Streaming, usage metering, or a model picker UI (a single configurable default model).

## Decisions

### D1. `ApiKey` model — one secret per type, write-only over the API

`world/models/api_key.py`: `api_type` (`TextChoices`, `OPENROUTER = "openrouter"`, **unique**),
`key_value` (`TextField`), `updated_at`, `updated_by`. One row per type (upsert on save).

- The DRF serializer marks `key_value` **write-only**; reads expose only `api_type`, `is_set`,
  a masked `key_preview` (`"…"+last4`), and `updated_at`. The raw secret is never serialized
  back — not on create, not on list.
- Curator-only (`IsCurator`) for every operation. Stored plaintext (per request); D-risk noted
  below.
- **Alternative considered:** env vars (like Inburgering). Rejected — the request is explicitly
  a curator-editable table so keys change without a redeploy.

### D2. OpenRouter client — thin `requests` wrapper, strict JSON reply

`world/utils/openrouter.py`: `generate_seo(description, source_lang, *, api_key, model)` POSTs
to `${OPENROUTER_BASE_URL}/chat/completions` (default `https://openrouter.ai/api/v1`) with the
key as a Bearer token, a system prompt pinning the task, and `response_format=json_object`. It
returns a validated dict of the SEO fields (bilingual). Network/parse/HTTP errors raise a
typed `OpenRouterError` the view maps to a clean 4xx/5xx. The model id is a settings default
(`OPENROUTER_MODEL`, env-overridable) so no schema churn to change models.

### D3. Generation is a preview, not a write

`POST /api/curation/seo/<key>/generate/` (curator-only action on `CurationSeoViewSet`):

1. Load the `openrouter` key → **409** with a clear message if absent.
2. Read the slot's resolved description: `description_es` if non-empty, else `description_en`
   → **400** "add a description first" if both blank.
3. Call `generate_seo`; on success return the generated set in the **same bilingual shape the
   editor already consumes** (`{title:{es,en}, description:{…}, og_title, og_description,
   keywords, image_alt}`).
4. The frontend fills the form from the response; the curator reviews and clicks **Save**
   (the existing `PATCH`). Nothing is persisted by the generate call itself.

- **Why preview-not-save:** LLM output needs a human check before it becomes the site's public
  metadata; it also lets the curator regenerate/tweak before committing.

### D4. Frontend — gated Generate button + an API Keys section

- **API Keys** dashboard section (curator-only): lists configured types with masked previews,
  lets the curator paste/replace a key or delete it. Uses the masked list + write-only save.
- **SeoTab**: a **Generate** button per slot, shown only when the `openrouter` key `is_set`
  (from a lightweight `curation/api-keys/` fetch). Click → `generateSeo(slot.key)` → populate
  the form (both languages) → curator Saves. Button shows a busy state and surfaces errors
  (no key / empty description / provider error) inline.

## Risks / Trade-offs

- **Plaintext secret in the DB** → Mitigation: curator-only access, write-only serializer,
  masked reads, secret used only server→OpenRouter, never sent to the browser. At-rest
  encryption is a follow-up. Also: whoever can read the DB can read the key — same trust level
  as env today.
- **LLM latency / failure** blocks the click → the call is synchronous with a bounded timeout;
  failures return a clear inline error and the curator can retry or fill fields manually.
- **Bad / non-JSON model output** → `response_format=json_object` + server-side validation;
  invalid shape becomes a clean "generation failed, try again", never a partial save.
- **Cost / abuse** → curator-only, one call per click, no batch. Usage caps are a follow-up.
- **Prompt-injected description** (curator-authored, low risk) → the description is treated as
  data in the user turn; the system prompt fixes the task and output schema.

## Migration Plan

1. Ship `ApiKey` + migration (empty table; feature simply dormant until a key is added).
2. Deploy; a curator adds an `openrouter` key in the new section. The Generate button then
   appears in the SEO tab. No env changes required (optional `OPENROUTER_MODEL` to override
   the default model).
3. **Rollback:** remove the endpoints/UI; the table can remain (unused) or be dropped. No
   public-facing data changes — generated values only exist once a curator saves them.

## Open Questions

- Model default: assume a cost-effective, capable general model id via `OPENROUTER_MODEL`
  (settable in env); confirm the preferred model when wiring.
- Should generation also fill `canonical`/`robots`? Assumed **no** — those are structural, not
  content, and stay manual.

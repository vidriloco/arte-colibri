"""OpenRouter client for generating SEO fields from a page description.

A thin `requests` wrapper over OpenRouter's OpenAI-compatible chat-completions
endpoint. The key is passed as a Bearer token and stays server-side. The reply is
forced to a JSON object and normalized into the bilingual SEO field shape the SEO
editor already consumes.
"""

import json
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# Curated allow-list: three models that are equivalent in price and power (the
# small/fast/cheap tier), one per major provider. The curator picks one; anything
# outside this list is rejected so a stray id can't run up cost.
SEO_MODELS = [
    {"id": "anthropic/claude-3.5-haiku", "label": "Claude 3.5 Haiku · Anthropic"},
    {"id": "openai/gpt-4o-mini", "label": "GPT-4o mini · OpenAI"},
    {"id": "google/gemini-2.0-flash-001", "label": "Gemini 2.0 Flash · Google"},
    {"id": "moonshotai/kimi-k2", "label": "Kimi K2 · Moonshot AI"},
]
ALLOWED_MODEL_IDS = [m["id"] for m in SEO_MODELS]
DEFAULT_MODEL = SEO_MODELS[0]["id"]

# The SEO fields we ask the model to produce, each as an {es,en} pair.
SEO_FIELDS = ["title", "description", "og_title", "og_description", "keywords", "image_alt"]

SYSTEM_PROMPT = (
    "You are an SEO assistant for Arte Colibrí, a curated bilingual (Spanish/English) "
    "online gallery of art by local artists in Mexico City. From the page description you "
    "are given, write concise, compelling SEO metadata in BOTH Spanish and English "
    "(translate as needed — never leave a language blank).\n\n"
    "Return ONLY a JSON object with exactly these keys, each an object with 'es' and 'en' "
    "string values:\n"
    '  "title"          — meta title, ~50-60 chars, may end with " — Arte Colibrí"\n'
    '  "description"    — meta description, ~120-160 chars\n'
    '  "og_title"       — social share title (can match title)\n'
    '  "og_description" — social share description (can match description)\n'
    '  "keywords"       — 5-8 comma-separated keywords\n'
    '  "image_alt"      — short alt text describing a representative share image\n'
    "No markdown, no commentary — just the JSON object."
)


class OpenRouterError(Exception):
    """Raised for any network/HTTP/parse failure talking to OpenRouter."""


def resolve_model(model):
    """Return a valid model id: the given one if allowed, else the code default."""
    return model if model in ALLOWED_MODEL_IDS else DEFAULT_MODEL


def generate_seo(description, source_lang, *, api_key, model=None, timeout=30):
    """Call OpenRouter and return the normalized bilingual SEO field dict.

    Raises OpenRouterError on any failure (network, non-200, unparseable body).
    """
    base = getattr(settings, "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    payload = {
        "model": resolve_model(model),
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Source language: {source_lang}\n"
                    f"Page description:\n{description}"
                ),
            },
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.6,
    }
    try:
        resp = requests.post(
            f"{base}/chat/completions",
            json=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                # OpenRouter recommends these for attribution; harmless if unset.
                "HTTP-Referer": getattr(settings, "SITE_BASE_URL", "https://artecolibri.mx"),
                "X-Title": "Arte Colibrí",
            },
            timeout=timeout,
        )
    except requests.RequestException as exc:
        raise OpenRouterError(f"OpenRouter request failed: {exc}") from exc

    if resp.status_code != 200:
        logger.warning("OpenRouter %s: %s", resp.status_code, resp.text[:300])
        raise OpenRouterError(f"OpenRouter returned HTTP {resp.status_code}.")

    try:
        content = resp.json()["choices"][0]["message"]["content"]
        data = json.loads(content)
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise OpenRouterError(f"Unparseable OpenRouter response: {exc}") from exc

    return _normalize(data)


def _normalize(data):
    """Coerce the model's JSON into `{field: {es, en}}` with plain strings."""
    if not isinstance(data, dict):
        raise OpenRouterError("OpenRouter response was not a JSON object.")
    out = {}
    for field in SEO_FIELDS:
        pair = data.get(field)
        if not isinstance(pair, dict):
            pair = {}
        out[field] = {
            "es": str(pair.get("es") or "").strip(),
            "en": str(pair.get("en") or "").strip(),
        }
    return out

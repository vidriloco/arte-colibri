"""Server-side Cloudflare Turnstile verification for public write endpoints."""

import requests
from django.conf import settings
from rest_framework.exceptions import ValidationError

VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


def verify(token):
    """True if the token passes siteverify.

    With no TURNSTILE_SECRET_KEY configured (dev, tests) verification is
    disabled and always passes. Network failures fail closed: a submission
    is rejected rather than letting an outage disable bot protection.
    """
    secret = settings.TURNSTILE_SECRET_KEY
    if not secret:
        return True
    if not token:
        return False
    try:
        res = requests.post(
            VERIFY_URL,
            data={"secret": secret, "response": token},
            timeout=5,
        )
        return bool(res.json().get("success"))
    except (requests.RequestException, ValueError):
        return False


def check_request(request):
    """Raise a DRF ValidationError unless the request carries a valid token."""
    if not verify(request.data.get("turnstile_token")):
        raise ValidationError(
            {"turnstile": ["Verification failed. Please try again."]}
        )

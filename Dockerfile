# syntax=docker/dockerfile:1
ARG PYTHON_VERSION=3.9

# ---- builder: compile Python deps (psycopg2 needs a C toolchain) ----
FROM python:${PYTHON_VERSION}-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install --no-install-recommends -y \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install deps into an isolated venv we can copy into the slim runtime stage.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# ---- runtime: slim image with only the shared libs the app loads ----
FROM python:${PYTHON_VERSION}-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# GeoDjango runtime libs (GDAL/GEOS/PROJ via gdal-bin) + psycopg2 runtime (libpq5).
# binutils lets ctypes locate libgdal. No build tools here — they stay in builder.
RUN apt-get update && apt-get install --no-install-recommends -y \
        binutils \
        gdal-bin \
        libproj-dev \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Run as a non-root user (uid 1000 commonly matches the host user for bind mounts).
RUN groupadd --gid 1000 app \
    && useradd --uid 1000 --gid app --create-home app

COPY --from=builder /opt/venv /opt/venv

WORKDIR /usr/src/app
COPY --chown=app:app . .

# Create the media dir owned by app so a fresh named volume mounted here
# initializes writable for the non-root runtime user.
RUN mkdir -p /usr/src/app/media && chown -R app:app /usr/src/app/media

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import sys,urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/').status < 500 else 1)" || exit 1

# Default = Django's dev server. The production compose override swaps this for
# gunicorn — which first needs `gunicorn` added to requirements.txt (left to you).
CMD ["python", "geodjango/manage.py", "runserver", "0.0.0.0:8000"]

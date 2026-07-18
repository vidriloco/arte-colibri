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

# ---- frontend-builder: compile the React SPA (Vite, base=/static/) ----
FROM node:24-alpine AS frontend-builder

WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

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

# Built SPA (dist is .dockerignored, so it always comes from the builder stage).
COPY --from=frontend-builder --chown=app:app /app/dist /usr/src/app/frontend/dist

# Create the media dir owned by app so a fresh named volume mounted here
# initializes writable for the non-root runtime user.
RUN mkdir -p /usr/src/app/media && chown -R app:app /usr/src/app/media

USER app

# Collect hashed static assets (SPA build + Django admin) into STATIC_ROOT at
# image build time, so every deploy ships ready-to-serve assets and no manual
# collectstatic step is needed. Needs no DB; default env values suffice.
RUN python geodjango/manage.py collectstatic --noinput

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import sys,urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/').status < 500 else 1)" || exit 1

# Default = Django's dev server. The production compose override swaps this for
# gunicorn.
CMD ["python", "geodjango/manage.py", "runserver", "0.0.0.0:8000"]

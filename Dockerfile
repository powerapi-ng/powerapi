# ---- Image configuration flags:
ARG POWERAPI_INSTALL_METHOD="pypi"
ARG POWERAPI_COMPONENTS="everything"
ARG POWERAPI_VERSION=""

# ---- Base stage (common setup):
FROM python:3-slim@sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419 AS base

RUN useradd -m -s /bin/bash powerapi
WORKDIR /home/powerapi

RUN python -m venv --clear /opt/powerapi-venv
ENV VIRTUAL_ENV=/opt/powerapi-venv PATH="/opt/powerapi-venv/bin:${PATH}"

# ---- Install PowerAPI package from PyPI.org:
FROM base AS pypi

ARG POWERAPI_COMPONENTS
ARG POWERAPI_VERSION

RUN python -m pip install --no-cache-dir "powerapi[${POWERAPI_COMPONENTS}]${POWERAPI_VERSION:+==$POWERAPI_VERSION}"

# ---- Install PowerAPI package from local sources (editable install):
FROM base AS local

ARG POWERAPI_COMPONENTS

COPY --chown=powerapi . /tmp/powerapi
RUN python -m pip install --no-cache-dir "/tmp/powerapi[${POWERAPI_COMPONENTS}]" && rm -r /tmp/powerapi

# ---- Final stage:
FROM ${POWERAPI_INSTALL_METHOD} AS final

ENTRYPOINT ["sh", "-c", "echo 'This container image is intended to be used as a base and should not be run directly.' >&2; exit 1"]

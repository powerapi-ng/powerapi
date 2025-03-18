FROM python:3-slim@sha256:8f3aba466a471c0ab903dbd7cb979abd4bda370b04789d25440cc90372b50e04

RUN useradd -m -s /bin/bash powerapi
WORKDIR /home/powerapi

RUN python -m venv --clear /opt/powerapi-venv
ENV VIRTUAL_ENV=/opt/powerapi-venv PATH="/opt/powerapi-venv/bin:$PATH"

COPY --chown=powerapi . /tmp/powerapi
RUN pip install --no-cache-dir "/tmp/powerapi[everything]" && rm -r /tmp/powerapi

ENTRYPOINT ["sh", "-c", "echo 'This container image should be used as a base image for a formula and is not intended to be run directly.' >&2; exit 1"]

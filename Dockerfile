FROM python:3-slim@sha256:8ac54da5710cdd31639bb66f5bc1888948fc2866c0b5b52913b4b33d8252e510

RUN useradd -m -s /bin/bash powerapi
WORKDIR /home/powerapi

RUN python -m venv --clear /opt/powerapi-venv
ENV VIRTUAL_ENV=/opt/powerapi-venv PATH="/opt/powerapi-venv/bin:$PATH"

COPY --chown=powerapi . /tmp/powerapi
RUN pip install --no-cache-dir "/tmp/powerapi[everything]" && rm -r /tmp/powerapi

ENTRYPOINT ["sh", "-c", "echo 'This container image should be used as a base image for a formula and is not intended to be run directly.' >&2; exit 1"]

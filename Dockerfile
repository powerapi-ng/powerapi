FROM python:3-slim@sha256:02699283cc784486281bb4bdf233b8cf443f038d9b9c91873d31bd4cbd622a3d

RUN useradd -m -s /bin/bash powerapi
WORKDIR /home/powerapi

RUN python -m venv --clear /opt/powerapi-venv
ENV VIRTUAL_ENV=/opt/powerapi-venv PATH="/opt/powerapi-venv/bin:$PATH"

COPY --chown=powerapi . /tmp/powerapi
RUN pip install --no-cache-dir "/tmp/powerapi[everything]" && rm -r /tmp/powerapi

ENTRYPOINT ["sh", "-c", "echo 'This container image should be used as a base image for a formula and is not intended to be run directly.' >&2; exit 1"]

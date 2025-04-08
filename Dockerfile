FROM python:3-slim@sha256:f2821f333099b62a286e6d0da85a89e29207a7b328d6c61660cf54334f5f2785

RUN useradd -m -s /bin/bash powerapi
WORKDIR /home/powerapi

RUN python -m venv --clear /opt/powerapi-venv
ENV VIRTUAL_ENV=/opt/powerapi-venv PATH="/opt/powerapi-venv/bin:$PATH"

COPY --chown=powerapi . /tmp/powerapi
RUN pip install --no-cache-dir "/tmp/powerapi[everything]" && rm -r /tmp/powerapi

ENTRYPOINT ["sh", "-c", "echo 'This container image should be used as a base image for a formula and is not intended to be run directly.' >&2; exit 1"]

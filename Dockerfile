FROM python:3-slim@sha256:6d79a6cfdec89007baad76f1184dfa7cf6075658730359e6d77b7515db2095c5

RUN useradd -d /opt/powerapi -m powerapi
WORKDIR /opt/powerapi
USER powerapi

COPY --chown=powerapi . /tmp/powerapi
RUN pip3 install --user --no-cache-dir "/tmp/powerapi[everything]" && rm -r /tmp/powerapi

ENTRYPOINT ["/bin/echo", "This Docker image should be used as a base for another image and should not be executed directly."]

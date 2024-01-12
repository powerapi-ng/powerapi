FROM python:3-slim@sha256:ee9a59cfdad294560241c9a8c8e40034f165feb4af7088c1479c2cdd84aafbed

RUN useradd -d /opt/powerapi -m powerapi
WORKDIR /opt/powerapi
USER powerapi

COPY --chown=powerapi . /tmp/powerapi
RUN pip3 install --user --no-cache-dir "/tmp/powerapi[everything]" && rm -r /tmp/powerapi

ENTRYPOINT ["/bin/echo", "This Docker image should be used as a base for another image and should not be executed directly."]

FROM python:3-slim@sha256:36d57d7f9948fefe7b6092cfe8567da368033e71ba281b11bb9eeffce3d45bc6

RUN useradd -d /opt/powerapi -m powerapi
WORKDIR /opt/powerapi
USER powerapi

COPY --chown=powerapi . /tmp/powerapi
RUN pip3 install --user --no-cache-dir "/tmp/powerapi[everything]" && rm -r /tmp/powerapi

ENTRYPOINT ["/bin/echo", "This Docker image should be used as a base for another image and should not be executed directly."]

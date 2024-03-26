FROM python:3-slim@sha256:5dc6f84b5e97bfb0c90abfb7c55f3cacc2cb6687c8f920b64a833a2219875997

RUN useradd -d /opt/powerapi -m powerapi
WORKDIR /opt/powerapi
USER powerapi

COPY --chown=powerapi . /tmp/powerapi
RUN pip3 install --user --no-cache-dir "/tmp/powerapi[everything]" && rm -r /tmp/powerapi

ENTRYPOINT ["/bin/echo", "This Docker image should be used as a base for another image and should not be executed directly."]

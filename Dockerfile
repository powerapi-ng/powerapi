FROM python:3.7

RUN useradd -d /opt/powerapi -m powerapi
WORKDIR /opt/powerapi
USER powerapi

COPY --chown=powerapi . /opt/powerapi/powerapi
RUN pip3 install --user --no-cache-dir -e "/opt/powerapi/powerapi[mongodb]"

ENTRYPOINT ["/bin/echo", "This Docker image should be used as a base for another image and should not be executed directly."]
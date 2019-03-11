FROM python:3.7

RUN useradd -d /opt/powerapi -m powerapi
WORKDIR /opt/powerapi
USER powerapi

# Put the Python dependencies into a layer to optimize the image build time
COPY --chown=powerapi requirements.txt /opt/powerapi/powerapi-requirements.txt
RUN pip3 install --user --no-cache-dir -r /opt/powerapi/powerapi-requirements.txt

COPY --chown=powerapi . /opt/powerapi/powerapi
RUN pip3 install --user --no-cache-dir --no-deps -e /opt/powerapi/powerapi

ENTRYPOINT ["/bin/echo", "This Docker image should be used as a base for another image and should not be executed directly."]
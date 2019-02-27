FROM fedora:29

RUN dnf -y update && \
    dnf -y install python3-setproctitle && \
    dnf clean all && \
    useradd -d /opt/powerapi -m powerapi

WORKDIR /opt/powerapi
USER powerapi

# Put the Python dependencies into a layer to optimize the image build time
COPY requirements.txt ./
RUN python3 -m pip install --user --no-cache-dir -r requirements.txt

COPY . ./
ENTRYPOINT ["python3", "powerapi-cli.py"]


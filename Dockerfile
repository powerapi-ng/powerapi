FROM fedora:29

WORKDIR /opt/powerapi

RUN dnf -y update && \
    dnf -y install python3-setproctitle && \
    dnf clean all

COPY . ./

RUN python3 -m pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python3", "./powerapi-cli.py"]

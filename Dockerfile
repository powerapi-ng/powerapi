FROM fedora:29

WORKDIR /opt/smartwatts

RUN dnf -y update && \
    dnf -y install python3-setproctitle && \
    dnf clean all

COPY . ./

RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python3", "./smartwatts-cli.py"]

# docker run --network=host smartwatts localhost 27017 smartwatts hwrep localhost 27017 sm_res sm_res19 SOCKET

# Copyright (c) 2021, INRIA
# Copyright (c) 2021, University of Lille
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.

# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.

# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
from datetime import datetime
from threading import Thread
from socket import socket
import json
import time

import pytest

from powerapi.database import SocketDB
from powerapi.report import HWPCReport
from powerapi.test_utils.report.hwpc import extract_rapl_reports_with_2_sockets


class ClientThread(Thread):

    def __init__(self, msg_list, port):
        Thread.__init__(self)

        self.msg_list = msg_list
        self.socket = socket()
        self.port = port

    def run(self):

        self.socket.connect(('localhost', self.port))
        for msg in self.msg_list:
            self.socket.send(bytes(json.dumps(msg), 'utf-8'))
        self.socket.close()


def assert_report_equals(hwpc_report, json_report):
    assert isinstance(hwpc_report,HWPCReport)
    assert hwpc_report.target == json_report['target']
    assert hwpc_report.timestamp == datetime.strptime(json_report['timestamp'], "%Y-%m-%dT%H:%M:%S.%f")
    assert hwpc_report.sensor == json_report['sensor']

    for group in hwpc_report.groups:
        assert hwpc_report.groups[group] == json_report['groups'][group]


@pytest.fixture
async def socket_db(unused_tcp_port):
    socket_db = SocketDB(HWPCReport, unused_tcp_port)
    await socket_db.connect()
    yield socket_db
    await socket_db.stop()


@pytest.mark.asyncio
async def test_read_one_json_object_received_from_the_socket(socket_db, unused_tcp_port):

    json_reports = extract_rapl_reports_with_2_sockets(1)
    client = ClientThread(json_reports, unused_tcp_port)
    client.start()

    iterator = socket_db.iter(False)

    report = await iterator.__anext__()
    assert_report_equals(report, json_reports[0])

@pytest.mark.asyncio
async def test_read_two_json_object_received_from_the_socket(socket_db, unused_tcp_port):
    json_reports = extract_rapl_reports_with_2_sockets(2)
    client = ClientThread(json_reports, unused_tcp_port)
    client.start()

    iterator = socket_db.iter(False)

    report = await iterator.__anext__()
    assert_report_equals(report, json_reports[0])

    report = await iterator.__anext__()
    assert_report_equals(report, json_reports[1])

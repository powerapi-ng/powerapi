# Copyright (c) 2024, INRIA
# Copyright (c) 2024, University of Lille
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

import pytest

from powerapi.database.http_db import HttpServerDB
from tests.integration.database.test_http_server import REPORT_TYPE
from tests.utils.report.hwpc import extract_rapl_reports_with_2_sockets


@pytest.fixture()
def server(host_token_port: tuple) -> HttpServerDB:
    """
    Create a server with the given host and REPORT_TYPE as report type and PORT as port
    :param host_token_port: Tuple (host, token) with the server host and the token to be defined when authentification is
    enabled
    """
    host = host_token_port[0]
    token = host_token_port[1]
    port = host_token_port[2]

    the_server = HttpServerDB(report_type=REPORT_TYPE, host=host, port=port, token=token)

    yield the_server

    the_server.disconnect()


@pytest.fixture()
def started_server(server) -> HttpServerDB:
    """
    Create and start a server with the given host and REPORT_TYPE as report type and PORT as port
    :param server: The server to be started
    """
    server.connect()

    yield server


@pytest.fixture()
def rest_client(started_server):
    """
    Return a client by using the provided server
    :param started_server The started server
    """
    app = started_server.flask_app
    with app.test_client() as client:
        yield client


@pytest.fixture()
def hwpc_reports(number_of_reports_to_extract: int):
    """
    Return a list of dicts, each one representing a hwpc report
    """
    return extract_rapl_reports_with_2_sockets(number_of_reports=number_of_reports_to_extract)

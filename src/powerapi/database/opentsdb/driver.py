# Copyright (c) 2025, Inria
# Copyright (c) 2025, University of Lille
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
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

from collections.abc import Iterable

from powerapi.database.driver import WritableDatabase
from powerapi.database.exceptions import ConnectionFailed, WriteFailed
from powerapi.database.opentsdb.codecs import ReportEncoders
from powerapi.report import Report

try:
    from opentsdb import TSDBClient, TSDBClientException
except ImportError:
    TSDBClient = None
    TSDBClientException = None


class OpenTSDB(WritableDatabase):
    """
    OpenTSDB database driver.
    Allow to persist reports to an OpenTSDB database.
    """

    def __init__(self, report_type: type[Report], host: str, port: int, metric_name: str):
        super().__init__()

        self._host = host
        self._port = port
        self._metric_name = metric_name

        self._client = TSDBClient(host, port, run_at_once=False)

        self._report_encoder = ReportEncoders.get(report_type)

    def connect(self) -> None:
        """
        Connect to the OpenTSDB server.
        :raise: ConnectionFailed if the connection to the OpenTSDB server fails
        """
        try:
            self._client.init_client(self._host, self._port)
            self._client.is_alive()
        except TSDBClientException as exn:
            raise ConnectionFailed(f'Failed to connect to the OpenTSDB server: {exn}') from exn

    def disconnect(self) -> None:
        """
        Disconnect from the OpenTSDB database.
        """
        self._client.close()

    @staticmethod
    def supported_write_types() -> Iterable[type[Report]]:
        """
        Return the report types that can be persisted to the OpenTSDB database.
        :return: Iterable of report types
        """
        return ReportEncoders.supported_types()

    def write(self, reports: Iterable[Report]) -> None:
        """
        Write the reports into the OpenTSDB database.
        :param reports: Iterable of reports
        :raise: WriteFailed if the write operation fails
        """
        try:
            # The OpenTSDB client library handle batching internally.
            for report in reports:
                value, tags = self._report_encoder.encode(report)
                self._client.send(self._metric_name, value, **tags)
        except TSDBClientException as exn:
            raise WriteFailed(f'Failed to save report to OpenTSDB database: {exn}') from exn

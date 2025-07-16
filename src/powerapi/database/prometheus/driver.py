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
from powerapi.database.exception import ConnectionFailed, WriteFailed
from powerapi.database.prometheus.codecs import ReportEncoders, EncoderOptions
from powerapi.database.prometheus.collectors import ReportProcessorFactory
from powerapi.report import Report

try:
    from prometheus_client import start_http_server, CollectorRegistry
except ImportError:
    start_http_server = None
    CollectorRegistry = None


class Prometheus(WritableDatabase):
    """
    Prometheus database driver.
    Allow to export reports as a Prometheus metrics endpoint.
    """

    def __init__(self, report_type: type[Report], listen_addr: str, listen_port: int, tags: list[str]):
        """
        :param report_type: Report type
        :param listen_addr: Address to listen on
        :param listen_port: Port to listen on
        :param tags: List of tags name that will be used by the metrics
        """
        super().__init__()

        self.listen_addr = (listen_addr, listen_port)
        self.tags = list(dict.fromkeys(['sensor', 'target', *tags]))  # Ensure unique tags name (and preserve order)

        self._http_server = None
        self._http_server_thread = None
        self._metrics_collector = ReportProcessorFactory.create_collector(report_type, self.tags)

        self._report_encoder = ReportEncoders.get(report_type)
        self._report_encoder_opts = EncoderOptions(self.tags)

    def connect(self) -> None:
        """
        Connect the Prometheus database.
        :raise: ConnectionFailed if the operation fails
        """
        try:
            registry = CollectorRegistry(auto_describe=True)
            registry.register(self._metrics_collector)

            addr, port = self.listen_addr
            self._http_server, self._http_server_thread = start_http_server(port, addr, registry=registry)
        except (OSError, RuntimeError) as exn:
            raise ConnectionFailed(f'Failed to connect the Prometheus database: {exn}') from exn

    def disconnect(self) -> None:
        """
        Disconnect the Prometheus database.
        """
        self._http_server.shutdown()
        self._http_server_thread.join()

    @staticmethod
    def supported_write_types() -> Iterable[type[Report]]:
        """
        Return the report types that can be persisted to the Prometheus database.
        :return: Iterable of report types
        """
        return ReportEncoders.supported_types()

    def write(self, reports: Iterable[Report]) -> None:
        """
        Write the reports into the Prometheus database.
        :param reports: Iterable of reports
        :raise: WriteFailed if the write operation fails
        """
        try:
            self._metrics_collector.submit(reports, self._report_encoder, self._report_encoder_opts)
        except (ValueError, TypeError) as exn:
            raise WriteFailed(f'Failed to save the report to Prometheus database: {exn}') from exn

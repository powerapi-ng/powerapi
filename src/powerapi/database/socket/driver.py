# Copyright (c) 2025, Inria
# Copyright (c) 2021, University of Lille
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
from queue import SimpleQueue, Empty
from threading import Thread

from powerapi.database.driver import ReadableDatabase
from powerapi.database.exceptions import ConnectionFailed
from powerapi.database.socket.codecs import ReportDecoders
from powerapi.database.socket.tcp_server import tcpserver_thread_target
from powerapi.report import Report


class Socket(ReadableDatabase):

    def __init__(self, report_type: type[Report], host: str, port: int):
        """
        :param report_type: The type of report to create
        :param host: The host address to listen on
        :param port: The port number to listen on
        """
        super().__init__()

        self.listen_addr = (host, port)

        self._report_decoder = ReportDecoders.get(report_type)

        self._received_data_queue: SimpleQueue[Report] | None = None
        self._tcp_server_thread: Thread | None = None

    def connect(self) -> None:
        """
        Connect the Socket database driver.
        :raise: ConnectionFailed if the operation fails
        """
        try:
            self._received_data_queue = SimpleQueue()
            thread_args = (self.listen_addr, self._received_data_queue)
            self._tcp_server_thread = Thread(target=tcpserver_thread_target, args=thread_args, daemon=True)
            self._tcp_server_thread.start()
        except RuntimeError as exn:
            raise ConnectionFailed(f'Failed to connect the Socket database: {exn}') from exn

    def disconnect(self) -> None:
        """
        Disconnect from the socket database.
        """

    @staticmethod
    def supported_read_types() -> Iterable[type[Report]]:
        """
        Return the report types that can be retrieved from the Socket database.
        :return: Iterable of report types
        """
        return ReportDecoders.supported_types()

    def read(self, stream_mode: bool = False) -> Iterable[Report]:
        """
        Read reports from the Socket database.
        :param stream_mode: No-Op for this database driver, steam mode is the only supported mode
        :return: Iterable of reports
        """
        while True:
            try:
                yield self._report_decoder.decode(self._received_data_queue.get(block=False))
            except Empty:
                break

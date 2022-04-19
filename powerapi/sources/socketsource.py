# Copyright (c) 2022, INRIA
# Copyright (c) 2022, University of Lille
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

# Author : Lauric Desauw
# Last modified : 13 April 2022

##############################
#
# Imports
#
##############################
import rx
from typing import Optional
from rx import Observable
from rx.core.typing import Scheduler, Observer
from powerapi.rx.source import BaseSource, Source
from powerapi.exception import SourceException
import powerapi.rx.report as papi_report
import socket
from powerapi.rx import JsonStream
import asyncio
from rx.scheduler.eventloop import AsyncIOScheduler


class SocketSource(BaseSource):
    def __init__(self, port: int) -> None:
        """Creates a source for TCP Socket

        Args:
        :param port: Port the server is lissening on

        """
        super().__init__()
        self.__name__ = "SocketSource"
        self.port = port

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.bind(("0.0.0.0", int(self.port)))
        except Exception as exn:
            raise SourceException(self.__name__, "cannot bind to socket") from exn

    # def subscribe(self, operator: Observer, scheduler: Optional[Scheduler] = None):
    #     # """Required method for retrieving data from a source by a Formula

    #     # Args:
    #     #     operator: The operator (e.g. a formula or log)  that will process the data
    #     #     scheduler: Used for parallelism. Not used for the time being

    #     # """
    #     try:
    #         stream = JsonStream(self.sock)
    #     except Exception as exn:
    #         raise SourceException(self.__name__, " cannot read from socket") from exn

    #     count = 0  # If 10 times in a row we don't have a full message we stop
    #     while True:
    #         json_str = stream.read_json_object()

    #         if json_str is None:
    #             if count > 10:
    #                 break
    #             count += 1
    #             continue
    #         count = 0

    #         report_dict = json.loads(json_str)
    #         (
    #             report_index,
    #             report_values,
    #             report_data,
    #         ) = papi_report.get_index_information_and_data_from_report_dict(report_dic)

    #         report = papi_report.Report(report_data, report_index, report_values)

    #         operator.on_next(report)

    def close(self):
        """Closes the socket"""
        self.sock.close()


def socket_source(port, loop):
    sink = SocketSource(port)

    def on_subscribe(observer, scheduler):
        async def handle_echo(reader, writer):
            print("handling echo")
            while True:
                data = await reader.readline()
                data = data.decode("utf-8")
                if not data:
                    break

                future = asyncio.Future()
                observer.on_next(EchoItem(future=future, data=data))
                await future
                writer.write(future.result().encode("utf-8"))

            writer.close()

        def on_next(i):
            i.future.set_result(i.data)

        print("start server")
        server = asyncio.start_server(handle_echo, "0.0.0.0", port, loop=loop)
        loop.create_task(server)

        sink.subscribe(
            on_next=on_next,
            on_error=observer.on_error,
            on_completed=observer.on_completed,
        )

    res = rx.create(on_subscribe)
    aio_scheduler = AsyncIOScheduler(loop=loop)
    return Source(res)

# Copyright (c) 2018, INRIA
# Copyright (c) 2018, University of Lille
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
import asyncio
from queue import Queue, Empty
from threading import Thread
from socket import socket

from . import IterDB, BaseDB
from powerapi.utils import JsonStream

BUFFER_SIZE = 4096
SOCKET_TIMEOUT = 0.5


class SocketDB(BaseDB):

    def __init__(self, port):
        BaseDB.__init__(self)
        self.asynchrone=True
        self.queue = None
        # self.loop = asyncio.get_event_loop()
        self.port = port
        self.server = None

    async def connect(self):
        self.queue = asyncio.Queue()
        # self.queue = Queue()
        self.server = await asyncio.start_server(self.gen_server_callback(), host='127.0.0.1', port=self.port)

    async def stop(self):
        self.server.close()
        await self.server.wait_closed()

    def iter(self, report_model, stream_mode):
        return IterSocketDB(report_model, stream_mode, self.queue)

    def gen_server_callback(self):
        async def callback(stream_reader, _):
            stream = JsonStream(stream_reader)
            while True:
                json_str = await stream.read_json_object()
                if json_str is None:
                    break
                await self.queue.put(json_str)
                # self.queue.put(json_str)

        return callback


class IterSocketDB(IterDB):
    """
    iterator connected to a socket that receive report from a sensor
    """

    def __init__(self, report_model, stream_mode, queue):
        """
        """
        IterDB.__init__(self, None, report_model, stream_mode)

        self.queue = queue

    def __aiter__(self):
        """
        """
        return self

    async def __anext__(self):
    # def __next__(self):
        """
        """
        try:
            json = await asyncio.wait_for(self.queue.get(), 2)
            # json = self.queue.get_nowait()
            # self.queue.get()
            report = self.report_model.get_type().deserialize(self.report_model.from_json(json))
            return report
        # except Empty:
        except asyncio.TimeoutError:
            return None

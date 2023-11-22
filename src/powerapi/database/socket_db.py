# Copyright (c) 2021, INRIA
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

import asyncio
from typing import Type, List
import json


from powerapi.utils import JsonStream
from powerapi.report import Report
from .base_db import IterDB, BaseDB, DBError

BUFFER_SIZE = 4096
SOCKET_TIMEOUT = 0.5


class SocketDB(BaseDB):
    """
    Database that act as a server that expose a socket where data source will push data
    """

    def __init__(self, report_type: Type[Report], port: int):
        BaseDB.__init__(self, report_type)
        self.asynchrone = True
        self.queue = None
        self.port = port
        self.server = None

    async def connect(self):
        self.queue = asyncio.Queue()
        self.server = await asyncio.start_server(self._gen_server_callback(), host='127.0.0.1', port=self.port)

    async def stop(self):
        """
        stop server connection
        """
        self.server.close()
        await self.server.wait_closed()

    def iter(self, stream_mode):
        return IterSocketDB(self.report_type, stream_mode, self.queue)

    def _gen_server_callback(self):
        async def callback(stream_reader, _):
            stream = JsonStream(stream_reader)
            count = 0  # If 10 times in a row we don't have a full message we stop
            while True:
                json_str = await stream.read_json_object()
                if json_str is None:
                    if count > 10:
                        break
                    count += 1
                    continue
                count = 0
                await self.queue.put(json_str)

                # self.queue.put(json_str)

        return callback

    def __iter__(self):
        raise DBError('Socket db don\'t support __iter__ method')

    def save(self, report: Report):
        raise DBError('Socket db don\'t support save method')

    def save_many(self, reports: List[Report]):
        raise DBError('Socket db don\'t support save_many method')


class IterSocketDB(IterDB):
    """
    iterator connected to a socket that receive report from a sensor
    """

    def __init__(self, report_type, stream_mode, queue):
        """
        """
        IterDB.__init__(self, None, report_type, stream_mode)

        self.queue = queue

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            json_str = await asyncio.wait_for(self.queue.get(), 2)
            # json = self.queue.get_nowait()
            # self.queue.get()
            report = self.report_type.from_json(json.loads(json_str))
            return report
        # except Empty:
        except asyncio.TimeoutError:
            return None

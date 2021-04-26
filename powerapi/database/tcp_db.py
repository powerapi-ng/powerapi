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
from threading import Thread, Lock
import socket

from . import IterDB, BaseDB
from powerapi.utils import JsonStream
from powerapi.report import Report
from powerapi.report_model import ReportModel


BUFFER_SIZE = 4096
SOCKET_TIMEOUT = 0.5

class IOTcpDB(BaseDB):

    def __init__(self, addr, port, input=False):
        self.lock = Lock()
        BaseDB.__init__(self)
        self.asynchrone = True
        
        self.loop = asyncio.get_event_loop()
        
        self.addr = addr
        self.port = port
        self.server = None
        self.clients = []
        self.in_client = None
        self.input = input
        
    async def connect(self):
        if self.input:
            # self.queue = Queue()
            self.in_client = await asyncio.open_connection (host=self.addr, port=self.port)        
        else:
            # self.queue = Queue()
            self.server = await asyncio.start_server(self.gen_server_callback(), host=self.addr, port=self.port, loop=self.loop)
        
    def stop(self):
        if self.input:
            self.client.close ()
        else:
            self.server.close()

    def save(self, report: Report, report_model: ReportModel):
        json = report.serialize ()
        with self.lock:        
            for i in range (0, len (self.clients)):
                if (self.clients [i].is_closing ()):
                    self.clients = self.clients [:i] + self.clients [i+1:]
                else:
                    self.clients [i].write (str (json).encode ())
        
    def save_many(self, reports, report_model):
        print (reports)
        for i in reports:
            self.save (i, report_model)

    def gen_server_callback(self):                
        def callback(_, writer):
            with self.lock:
                self.clients = self.clients + [writer]
            
        return callback

    def iter(self, report_model, stream_mode):
        return IterInTcpDB (self.in_client, report_model, stream_mode)


class IterInTcpDB(IterDB):

    def __init__ (self, db, report_model, stream_mode):
        IterDB.__init__ (self, None, report_model, stream_mode)
        
        self.db = db

    def __aiter__(self):
        """
        """
        return self
        
    async def __anext__ (self):
        reader, writer = self.db
        stream = JsonStream(reader)
        try: 
            json_str = await stream.read_json_object()
            report = self.report_model.get_type().deserialize(self.report_model.from_json(json_str))
            print (report, " ", json_str)
            return report
        except asyncio.TimeoutError:
            return None
        
                

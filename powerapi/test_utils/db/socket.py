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
import json
import time
from threading import Thread
from socket import socket


class ClientThread(Thread):
    """
    Thread that open a connection to a socket and send it a list of reports
    """

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


class ClientThreadDelay(Thread):
    """
    Thread that open a connection to a socket and send it a list of reports
    insert a delay of one second after sending half of the messages
    """

    def __init__(self, msg_list, port):
        Thread.__init__(self)

        self.msg_list = msg_list
        self.socket = socket()
        self.port = port

    def run(self):

        self.socket.connect(('localhost', self.port))
        midle = int(len(self.msg_list) / 2)
        for msg in self.msg_list[:midle]:
            self.socket.send(bytes(json.dumps(msg), 'utf-8'))
        time.sleep(1)
        for msg in self.msg_list[midle:]:
            self.socket.send(bytes(json.dumps(msg), 'utf-8'))
        self.socket.close()

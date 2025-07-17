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

import logging
from collections.abc import Iterator
from json import JSONDecoder, JSONDecodeError
from queue import SimpleQueue
from socketserver import ThreadingMixIn, TCPServer, StreamRequestHandler


class ThreadedTCPServer(ThreadingMixIn, TCPServer):
    """
    TCP Server implementation.
    Each client connected will be served by a separate thread.
    """
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, server_address, request_handler_class, received_data_queue: SimpleQueue):
        """
        :param server_address: The address to listen on
        :param request_handler_class: The request handler class to use when receiving requests
        :param received_data_queue: The data queue to store the received data
        """
        super().__init__(server_address, request_handler_class)
        self.received_data_queue = received_data_queue


class JsonRequestHandler(StreamRequestHandler):
    """
    Request handler that handles JSON documents received from the client.
    """
    server: ThreadedTCPServer

    @staticmethod
    def parse_json_documents(data: str) -> Iterator[dict]:
        """
        Try to parse json document(s) from the given string.
        This function tolerates truncated and malformed json documents.
        :param data: The raw data to decode
        :return: Iterator over parsed json documents
        """
        decoder = JSONDecoder()
        idx = 0
        while idx < len(data):
            try:
                obj, end_idx = decoder.raw_decode(data, idx)
                yield obj
                idx += end_idx

            # Search and try to parse the remaining document(s)
            except JSONDecodeError as e:
                idx = data.find('{', e.pos)
                if idx == -1:
                    break

    def handle(self):
        """
        Handle incoming connections.
        The received data is parsed and the result(s) stored in the data queue for further processing.
        It is expected for the data to be in json format (utf-8 charset) and newline terminated.
        """
        caddr = '{}:{}'.format(*self.client_address)
        logging.info('New incoming connection from %s', caddr)

        while True:
            try:
                data = self.rfile.readline()
                if not data:
                    break

                for obj in self.parse_json_documents(data.decode('utf-8')):
                    self.server.received_data_queue.put(obj)

            except ValueError as e:
                logging.warning('[%s] Received malformed data: %s', caddr, e)
                continue
            except OSError as e:
                logging.error('[%s] Caught OSError while handling request: %s', caddr, e)
                break
            except KeyboardInterrupt:
                break

        logging.info('Connection from %s closed', caddr)


def tcpserver_thread_target(listen_addr: tuple[str, int], received_data_queue: SimpleQueue) -> None:
    """
    Target function of the thread that will run the TCP server in background.
    :param listen_addr: The address to listen on (ip, port)
    :param received_data_queue: The queue where to store the received data
    """
    with ThreadedTCPServer(listen_addr, JsonRequestHandler, received_data_queue) as server:
        logging.info('TCP socket is listening on %s:%s', *listen_addr)
        server.serve_forever()

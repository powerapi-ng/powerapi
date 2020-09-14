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


DEFAULT_BUFFER_SIZE = 4096



class JsonStream:

    """read data received from a input utf-8 byte stream socket as a json stream

    :param stream_reader:
    :param buffer_size: size of the buffer used to receive data from the socket,
                        it must match the average size of received json string
                        (default 4096 bytes)
    """

    def __init__(self, stream_reader, buffer_size=DEFAULT_BUFFER_SIZE):
        self.stream_reader = stream_reader
        self.json_buffer = b''
        self.buffer_size = buffer_size

    def _extract_json_end_position(self):
        i = self.json_buffer.find(b'{') + 1
        open_brackets = 1

        while open_brackets != 0:
            if i >= len(self.json_buffer):
                return -1

            if self.json_buffer[i] == b'}'[0]:
                open_brackets -= 1
            elif self.json_buffer[i] == b'{'[0]:
                open_brackets += 1
            i += 1
        return i

    def _extract_json(self):
        i = self._extract_json_end_position()
        if i > 0:
            json_str = self.json_buffer[:i]
            self.json_buffer = self.json_buffer[i:]
            return json_str.decode('utf-8')
        else:
            return None

    async def _get_bytes(self):
        data = await self.stream_reader.read(n=self.buffer_size)
        return b'' if data is None else data

    async def _extract_big_json(self):
        stream_len = len(self.json_buffer)
        self.json_buffer += await self._get_bytes()

        if len(self.json_buffer) > stream_len:
            json_str = self._extract_json()
            if json_str is None:
                return self._extract_big_json()
            else:
                return json_str
        else:
            return None

    async def read_json_object(self):
        """
        return the first json object received from the connection as a string
        """
        self.json_buffer += await self._get_bytes()
        json_str = self._extract_json()
        if json_str is None:
            return await self._extract_big_json()
        else:
            return json_str

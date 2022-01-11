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

DEFAULT_BUFFER_SIZE = 4096


class JsonStream:
    """read data received from a input utf-8 byte stream socket as a json stream

    :param stream_reader:
    :param buffer_size: size of the buffer used to receive data from the socket,
                        it must match the average size of received json string
                        (default 4096 bytes)
    """

    def __init__(self, stream_reader, buffer_size=4096):
        self.stream_reader = stream_reader
        self.json_buffer = b''
        self.buffer_size = buffer_size
        self.open_brackets = 0

    async def _get_bytes(self):
        data = await self.stream_reader.read(n=self.buffer_size)
        return b'' if data is None else data

    def _extract_json_end_position(self, first_new_byte):
        """
        Find the first valable report in the stream
        """
        i = first_new_byte
        # print("buffer is ", self.json_buffer[first_new_byte:])
        if len(self.json_buffer) == 0:
            return -1
        if self.json_buffer[0] != 123:   # ASCII code opening bracket
            return -1

        while i < len(self.json_buffer):
            if self.json_buffer[i] == 125:  # ASCII code closing bracket
                self.open_brackets -= 1
                # print("opening : ", self.open_brackets)
            elif self.json_buffer[i] == 123:  # ASCII code opening bracket
                self.open_brackets += 1
                # print("closing :",self.open_brackets)
            if self.open_brackets == 0:
                return i
            i += 1

        return -1

    async def read_json_object(self):
        """
        return all the json object received from the connection as a iteration of string
        """
        if len(self.json_buffer) != 0 and self.open_brackets == 0:
            # Last iteration _extract_json_end_position returned a json_object
            # and breaked. If the buffer isn't empty wasn't treated, so we have
            # to treat it
            first_new_byte = 0
        else:
            first_new_byte = len(self.json_buffer)
            self.json_buffer += await self._get_bytes()
        i = self._extract_json_end_position(first_new_byte)

        if i == -1:
            return None
        if i == len(self.json_buffer) - 1:
            json_str = self.json_buffer[:]
            self.json_buffer = b''
            # print("buffer empty")
            # print(self.open_brackets)
        else:
            json_str = self.json_buffer[:i + 1]
            self.json_buffer = self.json_buffer[i + 1:]
            # print("buffer non empty ")
            # print(self.open_brackets)
        return json_str.decode('utf-8')

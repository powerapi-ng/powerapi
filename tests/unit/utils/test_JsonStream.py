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
import time
import asyncio

import pytest
from mock import Mock

from powerapi.utils import JsonStream

SOCKET_TIMEOUT = 0.2


class MockedStreamReader(Mock):
    def __init__(self, message):
        Mock.__init__(self)
        self.message = message

    async def read(self, n=-1):
        if self.message == '':
            time.sleep(SOCKET_TIMEOUT)
            return None
        else:
            byte_to_read = min(len(self.message), n)
            data = self.message[:byte_to_read]
            self.message = self.message[byte_to_read:]
            return bytes(data, 'utf-8')


def test_read_json_object_from_a_socket_without_data_return_None():
    socket = MockedStreamReader('')
    stream = JsonStream(socket)

    future = asyncio.ensure_future(stream.read_json_object())
    asyncio.get_event_loop().run_until_complete(future)
    assert future.result() is None


def test_read_json_object_from_a_socket_with_one_json_object_must_return_one_json_string():
    json_string = '{"a":1}'
    socket = MockedStreamReader(json_string)
    stream = JsonStream(socket)

    future = asyncio.ensure_future(stream.read_json_object())
    asyncio.get_event_loop().run_until_complete(future)
    assert future.result() == json_string


def test_read_json_object_twice_from_a_socket_with_one_json_object_must_return_only_one_json_string():
    json_string = '{"a":1}'
    socket = MockedStreamReader(json_string)
    stream = JsonStream(socket)

    future = asyncio.ensure_future(stream.read_json_object())
    asyncio.get_event_loop().run_until_complete(future)
    assert future.result() == json_string

    future = asyncio.ensure_future(stream.read_json_object())
    asyncio.get_event_loop().run_until_complete(future)
    assert future.result() is None


def test_read_json_object_from_a_socket_with_an_incomplete_json_object_must_return_None():
    json_string = '{"a":1'
    socket = MockedStreamReader(json_string)
    stream = JsonStream(socket)

    future = asyncio.ensure_future(stream.read_json_object())
    asyncio.get_event_loop().run_until_complete(future)
    assert future.result() is None


def test_read_json_object_from_a_socket_with_an_complete_json_object_and_incomplete_json_object_must_return_only_one_json_string():
    json_string = '{"a":1}{"a":1'
    socket = MockedStreamReader(json_string)
    stream = JsonStream(socket)

    future = asyncio.ensure_future(stream.read_json_object())
    asyncio.get_event_loop().run_until_complete(future)
    assert future.result() == '{"a":1}'

    future = asyncio.ensure_future(stream.read_json_object())
    asyncio.get_event_loop().run_until_complete(future)
    assert future.result() is None


def test_read_json_object_twice_from_a_socket_with_two_json_object_must_return_two_json_string():
    json1 = '{"a":1}'
    json2 = '{"b":2}'
    socket = MockedStreamReader(json1 + json2)
    stream = JsonStream(socket)

    future = asyncio.ensure_future(stream.read_json_object())
    asyncio.get_event_loop().run_until_complete(future)
    assert future.result() == json1

    future = asyncio.ensure_future(stream.read_json_object())
    asyncio.get_event_loop().run_until_complete(future)
    assert future.result() == json2

    future = asyncio.ensure_future(stream.read_json_object())
    asyncio.get_event_loop().run_until_complete(future)
    assert future.result() is None

# Copyright (c) 2024, Inria
# Copyright (c) 2024, University of Lille
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

import pytest

from powerapi.database.socket.tcp_server import JsonRequestHandler


def test_parse_json_empty_document():
    """
    Test parsing an empty JSON document.
    """
    document = ''
    results = JsonRequestHandler.parse_json_documents(document)

    with pytest.raises(StopIteration):
        next(results)


def test_parse_single_json_document():
    """
    Test parsing a single JSON document.
    """
    document = '''{"a": 1, "b": 2, "c": 3}'''
    results = JsonRequestHandler.parse_json_documents(document)

    first_result = next(results)

    assert first_result == {"a": 1, "b": 2, "c": 3}


def test_parse_single_invalid_json_document():
    """
    Test parsing a single invalid JSON document.
    """
    document = '''{"a": 1, "b": 2, "c":'''
    results = JsonRequestHandler.parse_json_documents(document)

    with pytest.raises(StopIteration):
        next(results)


def test_parse_multiple_json_documents():
    """
    Test parsing multiple JSON documents.
    """
    document = '''{"a": 1, "b": 2, "c": 3}{"d": 4, "e": 5, "f": 6}'''
    results = JsonRequestHandler.parse_json_documents(document)

    print(results)

    first_result = next(results)
    second_result = next(results)

    assert first_result == {"a": 1, "b": 2, "c": 3}
    assert second_result == {"d": 4, "e": 5, "f": 6}


def test_parse_multiple_documents_first_valid_second_invalid():
    """
    Test parsing multiple JSON documents where the first document is valid and second is invalid.
    """
    document = '''{"a": 1, "b": 2, "c": 3}{"d": 4, "e":'''
    results = JsonRequestHandler.parse_json_documents(document)

    first_result = next(results)
    assert first_result == {"a": 1, "b": 2, "c": 3}

    with pytest.raises(StopIteration):
        next(results)

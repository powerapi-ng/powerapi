# Copyright (c) 2026, Inria
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

from powerapi.config._utils import merge_dictionaries, string_to_bool, string_to_list


@pytest.mark.parametrize('value', [' YES ', 'y', 'true', 't', '1'])
def test_string_to_bool_converts_true_values(value):
    """
    Test that supported textual true values are normalized and converted.
    """
    assert string_to_bool(value) is True


@pytest.mark.parametrize('value', [' No ', 'n', 'false', 'f', '0'])
def test_string_to_bool_converts_false_values(value):
    """
    Test that supported textual false values are normalized and converted.
    """
    assert string_to_bool(value) is False


def test_string_to_bool_rejects_unknown_value():
    """
    Test that an unsupported textual boolean value is rejected.
    """
    with pytest.raises(ValueError, match='Invalid boolean value: invalid'):
        string_to_bool('invalid')


@pytest.mark.parametrize(('value', 'expected'), [
    ('', []),
    ('host', ['host']),
    ('host, pod', ['host', 'pod']),
])
def test_string_to_list_converts_comma_separated_values(value, expected):
    """
    Test that comma-separated values are split and stripped.
    """
    assert string_to_list(value) == expected


def test_merge_dictionaries_uses_last_configuration_as_highest_precedence():
    """
    Test that later configurations override earlier values while preserving nested values.
    """
    config_file = {'stream': False, 'input': {'sensor': {'port': 8080, 'uri': 'file'}}}
    environment = {'input': {'sensor': {'port': 9080}}}
    cli = {'stream': True, 'input': {'sensor': {'uri': 'cli'}}}

    result = merge_dictionaries(config_file, environment, cli)

    assert result == {
        'stream': True,
        'input': {'sensor': {'port': 9080, 'uri': 'cli'}},
    }


def test_merge_dictionaries_does_not_modify_or_reuse_inputs():
    """
    Test that merged dictionaries do not share mutable values with their inputs.
    """
    first = {'input': {'sensor': {'port': 8080, 'tags': ['host']}}}
    second = {'input': {'sensor': {'uri': 'socket'}}}

    result = merge_dictionaries(first, second)
    result['input']['sensor']['port'] = 9080
    result['input']['sensor']['tags'].append('socket')

    assert first == {'input': {'sensor': {'port': 8080, 'tags': ['host']}}}
    assert second == {'input': {'sensor': {'uri': 'socket'}}}

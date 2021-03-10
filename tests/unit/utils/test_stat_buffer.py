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

import pytest

from powerapi.utils import StatBuffer

M1 = {
    'tags': {'t1': 'a', 't2': 'b'},
    'time': 1,
    'value': 1.0
}

M2 = {
    'tags': {'t1': 'a', 't2': 'b'},
    'time': 2,
    'value': 2.0
}

M3 = {
    'tags': {'t1': 'a', 't2': 'b'},
    'time': 3,
    'value': 3.0
}

M4 = {
    'tags': {'t1': 'a', 't2': 'b'},
    'time': 4,
    'value': 4.0
}

def test_asking_if_stat_is_available_on_a_key_that_was_never_append_must_raise_KeyError():
    buffer = StatBuffer(3)

    buffer.append(M2, 'ab')
    with pytest.raises(KeyError):
        buffer.is_available('qlksjdq')


def test_asking_if_stat_is_available_on_a_stat_buffer_with_aggregation_periode_of_3_while_2_measure_where_append_on_2_seconds_return_false():
    buffer = StatBuffer(3)

    buffer.append(M1, 'ab')
    buffer.append(M2, 'ab')
    assert not buffer.is_available('ab')

def test_asking_if_stat_is_available_on_a_stat_buffer_with_aggregation_periode_of_1_while_2_measure_where_append_on_1_seconds_return_true():
    buffer = StatBuffer(1)

    buffer.append(M1, 'ab')
    buffer.append(M2, 'ab')
    assert buffer.is_available('ab')

def test_asking_if_stat_is_available_on_a_stat_buffer_with_aggregation_periode_of_1_while_2_measure_where_append_on_2_seconds_return_true():
    buffer = StatBuffer(1)

    buffer.append(M1, 'ab')
    buffer.append(M3, 'ab')
    assert buffer.is_available('ab')

def test_get_stats_on_a_stat_buffer_with_aggregation_periode_of_3_while_2_measure_where_append_on_2_seconds_return_None():
    buffer = StatBuffer(3)

    buffer.append(M1, 'ab')
    buffer.append(M2, 'ab')
    assert buffer.get_stats('ab') is None


def test_get_stats_on_a_key_that_was_never_append_must_raise_KeyError():
    buffer = StatBuffer(3)

    buffer.append(M2, 'ab')
    with pytest.raises(KeyError):
        buffer.get_stats('qlksjdq')


def test_get_stats_on_a_stat_buffer_with_aggregation_periode_of_1_while_2_measure_where_append_on_2_seconds_return_good_results():
    buffer = StatBuffer(1)

    buffer.append(M1, 'ab')
    buffer.append(M2, 'ab')
    assert buffer.get_stats('ab') == {
        'mean': 1.5,
        'std': 0.5,
        'min': 1.0,
        'max': 2.0,
        'tags': {'t1': 'a', 't2': 'b'},
        'time': 2
    }

def test_get_stats_on_a_stat_buffer_with_aggregation_periode_of_1_while_3_measure_where_append_on_2_seconds_return_stats_on_two_first_results():
    buffer = StatBuffer(1)

    buffer.append(M1, 'ab')
    buffer.append(M2, 'ab')
    buffer.append(M3, 'ab')
    assert buffer.get_stats('ab') == {
        'mean': 1.5,
        'std': 0.5,
        'min': 1.0,
        'max': 2.0,
        'tags': {'t1': 'a', 't2': 'b'},
        'time': 2
    }

def test_get_stats_second_times_on_a_stat_buffer_with_aggregation_periode_of_1_while_3_measure_where_append_on_2_seconds_return_None():
    buffer = StatBuffer(1)

    buffer.append(M1, 'ab')
    buffer.append(M2, 'ab')
    buffer.append(M3, 'ab')
    buffer.get_stats('ab')
    assert buffer.get_stats('ab') is None

def test_get_stats_second_times_on_a_stat_buffer_with_aggregation_periode_of_1_while_4_measure_where_append_on_2_seconds_return_good_result_for_two_last_measure():
    buffer = StatBuffer(1)

    buffer.append(M1, 'ab')
    buffer.append(M2, 'ab')
    buffer.append(M3, 'ab')
    buffer.append(M4, 'ab')
    buffer.get_stats('ab')
    assert buffer.get_stats('ab') == {
        'mean': 3.5,
        'std': 0.5,
        'min': 3.0,
        'max': 4.0,
        'tags': {'t1': 'a', 't2': 'b'},
        'time': 4
    }

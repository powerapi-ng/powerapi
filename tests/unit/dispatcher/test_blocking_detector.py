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
"""
This test will use a sequence of message that will be sent in alphabetical order:

  MessageA, MessageB, MessageC, MessageD, MessageE, MessageF

"""
import pytest

from powerapi.dispatcher.blocking_detector import BlockingDetector
from powerapi.report import Report


@pytest.fixture
def message_a():
    msg = Report(0, 'A', 'A')
    msg.dispatcher_report_id = 1
    return msg


@pytest.fixture
def message_b():
    msg = Report(1, 'B', 'B')
    msg.dispatcher_report_id = 2
    return msg


@pytest.fixture
def message_c():
    msg = Report(2, 'C', 'C')
    msg.dispatcher_report_id = 3
    return msg


@pytest.fixture
def message_d():
    msg = Report(3, 'D', 'D')
    msg.dispatcher_report_id = 4
    return msg


@pytest.fixture
def message_e():
    msg = Report(4, 'E', 'E')
    msg.dispatcher_report_id = 5
    return msg


@pytest.fixture
def message_f():
    msg = Report(5, 'F', 'F')
    msg.dispatcher_report_id = 6
    return msg


@pytest.fixture
def message_g():
    msg = Report(6, 'G', 'G')
    msg.dispatcher_report_id = 7
    return msg


def test_receive_poison_A_dont_make_blocked(message_a):
    blocking_detector = BlockingDetector()
    blocking_detector.notify_poison_received(message_a)
    assert not blocking_detector.is_blocked()


def test_receive_poison_A_and_B_dont_make_blocked(message_a, message_b):
    blocking_detector = BlockingDetector()
    blocking_detector.notify_poison_received(message_a)
    blocking_detector.notify_poison_received(message_b)
    assert not blocking_detector.is_blocked()


def test_receive_poison_A_B_and_C_make_blocked(message_a, message_b, message_c):
    blocking_detector = BlockingDetector()
    blocking_detector.notify_poison_received(message_a)
    blocking_detector.notify_poison_received(message_b)
    blocking_detector.notify_poison_received(message_c)
    assert blocking_detector.is_blocked()


def test_receive_poison_A_B_C_and_D_dont_make_blocked(message_a, message_b, message_c, message_d):
    blocking_detector = BlockingDetector()
    blocking_detector.notify_poison_received(message_a)
    blocking_detector.notify_poison_received(message_b)
    blocking_detector.notify_poison_received(message_c)
    blocking_detector.notify_poison_received(message_d)
    assert not blocking_detector.is_blocked()


def test_receive_poison_A_B_C_D_and_E_dont_make_blocked(message_a, message_b, message_c, message_d, message_e):
    blocking_detector = BlockingDetector()
    blocking_detector.notify_poison_received(message_a)
    blocking_detector.notify_poison_received(message_b)
    blocking_detector.notify_poison_received(message_c)
    blocking_detector.notify_poison_received(message_d)
    blocking_detector.notify_poison_received(message_e)
    assert not blocking_detector.is_blocked()


def test_receive_poison_A_B_C_D_E_and_F_dont_make_blocked(message_a, message_b, message_c, message_d, message_e,
                                                          message_f):
    blocking_detector = BlockingDetector()
    blocking_detector.notify_poison_received(message_a)
    blocking_detector.notify_poison_received(message_b)
    blocking_detector.notify_poison_received(message_c)
    blocking_detector.notify_poison_received(message_d)
    blocking_detector.notify_poison_received(message_e)
    blocking_detector.notify_poison_received(message_f)
    assert not blocking_detector.is_blocked()


def test_receive_poison_A_and_C_dont_make_blocked(message_a, message_c):
    blocking_detector = BlockingDetector()
    blocking_detector.notify_poison_received(message_a)
    blocking_detector.notify_poison_received(message_c)
    assert not blocking_detector.is_blocked()


def test_receive_poison_A_C_and_D_dont_make_blocked(message_a, message_c, message_d):
    blocking_detector = BlockingDetector()
    blocking_detector.notify_poison_received(message_a)
    blocking_detector.notify_poison_received(message_c)
    blocking_detector.notify_poison_received(message_d)
    assert not blocking_detector.is_blocked()


def test_receive_poison_A_C_D_and_E_make_blocked(message_a, message_c, message_d, message_e):
    blocking_detector = BlockingDetector()
    blocking_detector.notify_poison_received(message_a)
    blocking_detector.notify_poison_received(message_c)
    blocking_detector.notify_poison_received(message_d)
    blocking_detector.notify_poison_received(message_e)
    assert blocking_detector.is_blocked()


def test_receive_poison_A_C_D_E_and_F_dont_make_blocked(message_a, message_c, message_d, message_e, message_f):
    blocking_detector = BlockingDetector()
    blocking_detector.notify_poison_received(message_a)
    blocking_detector.notify_poison_received(message_c)
    blocking_detector.notify_poison_received(message_d)
    blocking_detector.notify_poison_received(message_e)
    blocking_detector.notify_poison_received(message_f)
    assert not blocking_detector.is_blocked()


def test_receive_poison_A_B_and_D_dont_make_blocked(message_a, message_b, message_d):
    blocking_detector = BlockingDetector()
    blocking_detector.notify_poison_received(message_a)
    blocking_detector.notify_poison_received(message_b)
    blocking_detector.notify_poison_received(message_d)
    assert not blocking_detector.is_blocked()


def test_receive_poison_A_B_D_and_E_dont_make_blocked(message_a, message_b, message_d, message_e):
    blocking_detector = BlockingDetector()
    blocking_detector.notify_poison_received(message_a)
    blocking_detector.notify_poison_received(message_b)
    blocking_detector.notify_poison_received(message_d)
    blocking_detector.notify_poison_received(message_e)
    assert not blocking_detector.is_blocked()


def test_receive_poison_A_B_D_E_and_F_make_blocked(message_a, message_b, message_d, message_e, message_f):
    blocking_detector = BlockingDetector()
    blocking_detector.notify_poison_received(message_a)
    blocking_detector.notify_poison_received(message_b)
    blocking_detector.notify_poison_received(message_d)
    blocking_detector.notify_poison_received(message_e)
    blocking_detector.notify_poison_received(message_f)
    assert blocking_detector.is_blocked()


def test_receive_poison_A_B_D_E_F_and_G_dont_make_blocked(message_a, message_b, message_d, message_e, message_f,
                                                          message_g):
    blocking_detector = BlockingDetector()
    blocking_detector.notify_poison_received(message_a)
    blocking_detector.notify_poison_received(message_b)
    blocking_detector.notify_poison_received(message_d)
    blocking_detector.notify_poison_received(message_e)
    blocking_detector.notify_poison_received(message_f)
    blocking_detector.notify_poison_received(message_g)
    assert not blocking_detector.is_blocked()


def test_receive_poison_A_B_and_C_with_B_sup_to_max_id_make_blocked(message_a, message_b, message_c):
    message_a.dispatcher_report_id = 10000
    message_b.dispatcher_report_id = 0
    message_c.dispatcher_report_id = 1
    blocking_detector = BlockingDetector()
    blocking_detector.notify_poison_received(message_a)
    blocking_detector.notify_poison_received(message_b)
    blocking_detector.notify_poison_received(message_c)
    assert blocking_detector.is_blocked()

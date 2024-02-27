# Copyright (c) 2021, Inria
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

import datetime

from powerapi.dispatcher.blocking_detector import BlockingDetector
from powerapi.report import Report


def generate_report(sensor: str, report_id: int):
    """
    Generate a report to test the blocking detector.
    """
    msg = Report(datetime.datetime.fromtimestamp(0, tz=datetime.timezone.utc), sensor, 'pytest')
    msg.dispatcher_report_id = report_id
    return msg


def test_receive_poison_A_dont_make_blocked():
    """
    Check that the BlockingDetector is not blocked with a first received message
    """
    blocking_detector = BlockingDetector()
    blocking_detector.notify_poison_received(generate_report('A', 1))
    assert not blocking_detector.is_blocked()


def test_receive_poison_A_and_B_dont_make_blocked():
    """
    Check that the BlockingDetector is not blocked with two received messages
    """
    blocking_detector = BlockingDetector()
    blocking_detector.notify_poison_received(generate_report('A', 1))
    blocking_detector.notify_poison_received(generate_report('B', 2))
    assert not blocking_detector.is_blocked()


def test_receive_poison_A_B_and_C_make_blocked():
    """
    Check that the BlockingDetector is blocked with three received messages with consecutive ids
    """
    blocking_detector = BlockingDetector()
    blocking_detector.notify_poison_received(generate_report('A', 1))
    blocking_detector.notify_poison_received(generate_report('B', 2))
    blocking_detector.notify_poison_received(generate_report('C', 3))
    assert blocking_detector.is_blocked()


def test_receive_poison_A_B_C_and_D_dont_make_blocked():
    """
    Check that the BlockingDetector is blocked with more than 2 received messages with consecutive ids
    """
    blocking_detector = BlockingDetector()
    blocking_detector.notify_poison_received(generate_report('A', 1))
    blocking_detector.notify_poison_received(generate_report('B', 2))
    blocking_detector.notify_poison_received(generate_report('C', 3))
    blocking_detector.notify_poison_received(generate_report('D', 4))
    assert not blocking_detector.is_blocked()


def test_receive_poison_A_B_C_D_and_E_dont_make_blocked():
    """
    Check that the BlockingDetector is blocked with more than 2 received messages with consecutive ids
    """
    blocking_detector = BlockingDetector()
    blocking_detector.notify_poison_received(generate_report('A', 1))
    blocking_detector.notify_poison_received(generate_report('B', 2))
    blocking_detector.notify_poison_received(generate_report('C', 3))
    blocking_detector.notify_poison_received(generate_report('D', 4))
    blocking_detector.notify_poison_received(generate_report('E', 5))
    assert not blocking_detector.is_blocked()


def test_receive_poison_A_B_C_D_E_and_F_dont_make_blocked():

    """
    Check that the BlockingDetector is blocked with more than 2 received messages with consecutive ids
    """
    blocking_detector = BlockingDetector()
    blocking_detector.notify_poison_received(generate_report('A', 1))
    blocking_detector.notify_poison_received(generate_report('B', 2))
    blocking_detector.notify_poison_received(generate_report('C', 3))
    blocking_detector.notify_poison_received(generate_report('D', 4))
    blocking_detector.notify_poison_received(generate_report('E', 5))
    blocking_detector.notify_poison_received(generate_report('F', 6))
    assert not blocking_detector.is_blocked()


def test_receive_poison_A_and_C_dont_make_blocked():
    """
    Check that the BlockingDetector is not blocked with 2 received messages with not consecutive ids
    """
    blocking_detector = BlockingDetector()
    blocking_detector.notify_poison_received(generate_report('A', 1))
    blocking_detector.notify_poison_received(generate_report('C', 3))
    assert not blocking_detector.is_blocked()


def test_receive_poison_A_C_and_D_dont_make_blocked():
    """
    Check that the BlockingDetector is not blocked with 3 received messages, one with not consecutive id
    """
    blocking_detector = BlockingDetector()
    blocking_detector.notify_poison_received(generate_report('A', 1))
    blocking_detector.notify_poison_received(generate_report('C', 3))
    blocking_detector.notify_poison_received(generate_report('D', 4))
    assert not blocking_detector.is_blocked()


def test_receive_poison_A_C_D_and_E_make_blocked():
    """
    Check that the BlockingDetector is blocked with 4 received messages, one with not consecutive id
    """
    blocking_detector = BlockingDetector()
    blocking_detector.notify_poison_received(generate_report('A', 1))
    blocking_detector.notify_poison_received(generate_report('C', 3))
    blocking_detector.notify_poison_received(generate_report('D', 4))
    blocking_detector.notify_poison_received(generate_report('E', 5))
    assert blocking_detector.is_blocked()


def test_receive_poison_A_C_D_E_and_F_dont_make_blocked():
    """
    Check that the BlockingDetector is blocked with more than 4 received messages, one with not consecutive id
    """
    blocking_detector = BlockingDetector()
    blocking_detector.notify_poison_received(generate_report('A', 1))
    blocking_detector.notify_poison_received(generate_report('C', 3))
    blocking_detector.notify_poison_received(generate_report('D', 4))
    blocking_detector.notify_poison_received(generate_report('E', 5))
    blocking_detector.notify_poison_received(generate_report('F', 6))
    assert not blocking_detector.is_blocked()


def test_receive_poison_A_B_and_D_dont_make_blocked():
    """
    Check that the BlockingDetector is not blocked with 3 received messages, one with not consecutive id
    """
    blocking_detector = BlockingDetector()
    blocking_detector.notify_poison_received(generate_report('A', 1))
    blocking_detector.notify_poison_received(generate_report('B', 2))
    blocking_detector.notify_poison_received(generate_report('D', 4))
    assert not blocking_detector.is_blocked()


def test_receive_poison_A_B_D_and_E_dont_make_blocked():
    """
    Check that the BlockingDetector is not blocked with 4 received messages, one with not consecutive id
    """
    blocking_detector = BlockingDetector()
    blocking_detector.notify_poison_received(generate_report('A', 1))
    blocking_detector.notify_poison_received(generate_report('B', 2))
    blocking_detector.notify_poison_received(generate_report('D', 4))
    blocking_detector.notify_poison_received(generate_report('E', 5))
    assert not blocking_detector.is_blocked()


def test_receive_poison_A_B_D_E_and_F_make_blocked():
    """
    Check that the BlockingDetector is blocked with more than 4 received messages, one with not consecutive id
    """
    blocking_detector = BlockingDetector()
    blocking_detector.notify_poison_received(generate_report('A', 1))
    blocking_detector.notify_poison_received(generate_report('B', 2))
    blocking_detector.notify_poison_received(generate_report('D', 4))
    blocking_detector.notify_poison_received(generate_report('E', 5))
    blocking_detector.notify_poison_received(generate_report('F', 6))
    assert blocking_detector.is_blocked()


def test_receive_poison_A_B_D_E_F_and_G_dont_make_blocked():
    """
    Check that the BlockingDetector is blocked with more than 4 received messages, one with not consecutive id
    """
    blocking_detector = BlockingDetector()
    blocking_detector.notify_poison_received(generate_report('A', 1))
    blocking_detector.notify_poison_received(generate_report('B', 2))
    blocking_detector.notify_poison_received(generate_report('D', 4))
    blocking_detector.notify_poison_received(generate_report('E', 5))
    blocking_detector.notify_poison_received(generate_report('F', 6))
    blocking_detector.notify_poison_received(generate_report('G', 7))
    assert not blocking_detector.is_blocked()


def test_receive_poison_A_B_and_C_with_B_sup_to_max_id_make_blocked():
    """
    Check that the BlockingDetector is blocked with 3 received messages, one with max_id_value
    """
    blocking_detector = BlockingDetector()
    blocking_detector.notify_poison_received(generate_report('A', 10000))
    blocking_detector.notify_poison_received(generate_report('B', 0))
    blocking_detector.notify_poison_received(generate_report('C', 1))
    assert blocking_detector.is_blocked()

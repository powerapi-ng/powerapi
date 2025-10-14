# Copyright (c) 2023, INRIA
# Copyright (c) 2023, University of Lille
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
import os
from datetime import datetime, timezone

import pytest

from powerapi.actor.message import StartMessage, ErrorMessage, OKMessage
from powerapi.database import ReadableDatabase
from powerapi.filter import Filter
from powerapi.puller import PullerActor
from powerapi.report import Report
from tests.utils.db import SilentFakeDB
from tests.utils.dispatcher import FakeDispatcher


def _setup_fake_database(num_reports: int = 5):
    """
    Set up a fake database for tests.
    """
    return SilentFakeDB([Report(datetime.fromtimestamp(i, timezone.utc), 'pytest', f'report-{i}') for i in range(num_reports)])


def _setup_puller_actor(name: str, database: ReadableDatabase, report_filter: Filter, stream_mode: bool = False):
    """
    Set up a PullerActor for tests.
    """
    puller = PullerActor(name, database, report_filter, stream_mode, logging.DEBUG)
    puller.start()
    puller.connect_control()
    puller.connect_data()
    return puller


def test_puller_start_message_empty_filter():
    """
    Test that the puller send an ErrorMessage when it receives a StartMessage with an empty filter.
    """
    report_filter = Filter()
    puller = _setup_puller_actor('puller_test_start_message_empty_filter', _setup_fake_database(), report_filter)
    assert puller.is_alive() is True

    puller.send_control(StartMessage())
    message = puller.receive_control()
    assert isinstance(message, ErrorMessage)

    puller.terminate()
    puller.join(timeout=5.0)
    assert puller.is_alive() is False


def test_puller_send_reports_to_dispatcher():
    """
    Test that the puller send reports to the dispatcher when it receives a StartMessage.
    """
    dispatcher = FakeDispatcher('dispatcher_test_send_reports_to_dispatcher')

    report_filter = Filter()
    report_filter.filter(lambda msg: True, dispatcher)

    num_reports = 10
    database = _setup_fake_database(num_reports)

    puller = _setup_puller_actor('puller_test_send_reports_to_dispatcher', database, report_filter)
    assert puller.is_alive() is True

    puller.send_control(StartMessage())
    message = puller.receive_control()
    assert isinstance(message, OKMessage)

    puller.join(timeout=5.0)
    assert puller.is_alive() is False
    assert dispatcher.get_num_received_data() == num_reports


def test_puller_with_multiple_reports_filter():
    """
    Test that the puller follow defined filter when sending the reports to the dispatcher.
    """
    dispatcher_even = FakeDispatcher('even_dispatcher_test_with_multiple_reports_filter')
    dispatcher_odd = FakeDispatcher('odd_dispatcher_test_with_multiple_reports_filter')
    dispatcher_catch_all = FakeDispatcher('catchall_dispatcher_test_with_multiple_reports_filter')

    num_reports = 10
    database = _setup_fake_database(num_reports)

    report_filter = Filter()
    report_filter.filter(lambda msg: (int(msg.target.removeprefix('report-')) % 2) == 0, dispatcher_even)
    report_filter.filter(lambda msg: (int(msg.target.removeprefix('report-')) % 2) != 0, dispatcher_odd)
    report_filter.filter(lambda msg: True, dispatcher_catch_all)

    puller = _setup_puller_actor('puller_test_with_multiple_reports_filter', database, report_filter)
    assert puller.is_alive() is True

    puller.send_control(StartMessage())
    message = puller.receive_control()
    assert isinstance(message, OKMessage)

    puller.join(timeout=5.0)
    assert puller.is_alive() is False
    assert dispatcher_even.get_num_received_data() == 5  # 0, 2, 4, 6, 8
    assert dispatcher_odd.get_num_received_data() == 5  # 1, 3, 5, 7, 9
    assert dispatcher_catch_all.get_num_received_data() == num_reports


@pytest.mark.skipif(os.getenv("CI") == "true", reason="This test is too flaky to be run in CI")
def test_puller_with_stream_mode():
    """
    Test that the puller send reports to the dispatcher and stay alive waiting for new reports.
    """
    dispatcher = FakeDispatcher('dispatcher_test_with_stream_mode')

    report_filter = Filter()
    report_filter.filter(lambda msg: True, dispatcher)

    num_reports = 10
    database = _setup_fake_database(num_reports)

    puller = _setup_puller_actor('puller_test_with_stream_mode', database, report_filter, stream_mode=True)
    assert puller.is_alive() is True

    puller.send_control(StartMessage())
    message = puller.receive_control()
    assert isinstance(message, OKMessage)

    puller.join(timeout=5.0)
    assert puller.is_alive() is True
    assert dispatcher.get_num_received_data() == num_reports

    puller.terminate()
    puller.join(timeout=5.0)
    assert puller.is_alive() is False

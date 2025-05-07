# Copyright (c) 2022, Inria
# Copyright (c) 2022, University of Lille
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
import time
from queue import Empty

import pytest

from powerapi.pusher import PusherActor
from powerapi.report import Report
from tests.unit.actor.abstract_test_actor import AbstractTestActorWithDB, pytest_generate_tests_abstract
from tests.utils.db.db import REPORT2, REPORT1


def define_buffer_size(size):
    """
    Define the buffer size by using the given parameter
    :param size: The buffer size
    """

    def wrap(func):
        func._buffer_size = size
        return func

    return wrap


def define_delay(delay):
    """
    Define the delay by using the given parameter
    :param delay; The delay
    """

    def wrap(func):
        func._delay = delay
        return func

    return wrap


def pytest_generate_tests(metafunc):
    """
    Function called by pytest when collecting a test_XXX function

    define the content fixtures in test environement with collected the
    value _content if it exist or with an empty content

    :param metafunc: the test context given by pytest
    """
    pytest_generate_tests_abstract(metafunc)

    if 'buffer_size' in metafunc.fixturenames:
        buffer_size = getattr(metafunc.function, '_buffer_size', None)
        if isinstance(buffer_size, int):
            metafunc.parametrize('buffer_size', [buffer_size])
        else:
            metafunc.parametrize('buffer_size', [50])

    if 'delay' in metafunc.fixturenames:
        delay = getattr(metafunc.function, '_delay', None)
        if isinstance(delay, int):
            metafunc.parametrize('delay', [delay])
        else:
            metafunc.parametrize('delay', [100])


class TestPusher(AbstractTestActorWithDB):
    """
    Class for testing PusherActor
    """

    @pytest.fixture
    def actor_with_db(self, fake_db, delay, buffer_size):
        return PusherActor('pusher_test', Report, fake_db, logging.DEBUG, delay=delay, max_size=buffer_size)

    @staticmethod
    @define_buffer_size(0)
    def test_send_one_report_to_pusher_with_0_sized_buffer_make_it_save_the_report(started_actor_with_db, fake_db):
        """
        Check that the pusher actor saves a report when the buffer size is 0.
        """
        started_actor_with_db.send_data(REPORT1)
        assert fake_db.q.get(timeout=1) == [REPORT1]

    @staticmethod
    @define_buffer_size(1)
    def test_send_one_report_to_pusher_with_1_sized_buffer_make_it_not_save_the_report(started_actor_with_db, fake_db):
        """
        Check that the pusher actor does not save a report when the buffer size is 1.
        """
        started_actor_with_db.send_data(REPORT1)
        with pytest.raises(Empty):
            fake_db.q.get(timeout=1)

    @staticmethod
    @define_buffer_size(1)
    def test_send_two_report_to_pusher_with_1_sized_buffer_make_it_save_the_reports_in_one_call(started_actor_with_db, fake_db):
        """
        Check that the pusher actor saves the 2 reports when the buffer size is 1.
        """
        started_actor_with_db.send_data(REPORT1)
        started_actor_with_db.send_data(REPORT2)
        assert fake_db.q.get(timeout=1) == [REPORT1, REPORT2]

    @staticmethod
    @define_delay(0)
    def test_send_one_report_to_pusher_with_0_delay_make_it_save_the_reports(started_actor_with_db, fake_db):
        """
        Check that the pusher actor saves a report when the delay is 0.
        """
        started_actor_with_db.send_data(REPORT1)
        assert fake_db.q.get(timeout=1) == [REPORT1]

    @staticmethod
    @define_delay(2000)
    def test_send_two_report_to_pusher_with_2_seconds_delay_make_it_not_save_the_reports(started_actor_with_db, fake_db):
        """
        Check that the pusher actor does not save the 2 reports when delay is 2 seconds.
        """
        started_actor_with_db.send_data(REPORT1)
        started_actor_with_db.send_data(REPORT2)
        with pytest.raises(Empty):
            fake_db.q.get(timeout=1)

    @staticmethod
    @define_delay(2000)
    def test_send_two_report__with_two_second_between_messages_to_pusher_with_2_seconds_delay_make_it_save_the_report(started_actor_with_db, fake_db):
        """
        Check that the pusher actor saves the 2 reports when delay is 2 seconds and there is a 2 second sleep time between the 2 reports.
        """
        started_actor_with_db.send_data(REPORT1)
        time.sleep(2)
        started_actor_with_db.send_data(REPORT2)
        assert fake_db.q.get(timeout=1) == [REPORT1, REPORT2]

    @staticmethod
    @define_buffer_size(1)
    def test_send_two_report_in_wrong_time_order_to_a_pusher_make_it_save_them_in_good_order(started_actor_with_db, fake_db):
        """
        Check that the pusher actor saves the 2 reports in the correct order even if they are not sent in the correct order.
        """
        started_actor_with_db.send_data(REPORT2)
        started_actor_with_db.send_data(REPORT1)
        assert fake_db.q.get(timeout=1) == [REPORT1, REPORT2]

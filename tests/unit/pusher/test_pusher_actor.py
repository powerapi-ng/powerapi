"""
Copyright (c) 2018, INRIA
Copyright (c) 2018, University of Lille
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""


import logging
import time
from queue import Empty
from mock import Mock

import pytest

from powerapi.report import Report
from powerapi.pusher import PusherActor

from ..actor.abstract_test_actor import AbstractTestActor
from ..db_utils import FakeDB, AbstractTestActorWithDB, REPORT1, REPORT2


def define_buffer_size(size):
    def wrap(func):
        setattr(func, '_buffer_size', size)
        return func
    return wrap

def define_delay(delay):
    def wrap(func):
        setattr(func, '_delay', delay)
        return func
    return wrap

def pytest_generate_tests(metafunc):
    """
    Function called by pytest when collecting a test_XXX function

    define the content fixtures in test environement with collected the
    value _content if it exist or with an empty content

    :param metafunc: the test context given by pytest
    """
    if 'content' in metafunc.fixturenames:
        content = getattr(metafunc.function, '_content', None)
        if isinstance(content, list):
            metafunc.parametrize('content', [content])
        else:
            metafunc.parametrize('content', [[]])

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


class TestPuller(AbstractTestActorWithDB):

    @pytest.fixture
    def fake_db(self, content):
        return FakeDB(content)

    @pytest.fixture
    def actor(self, fake_db, buffer_size, delay):
        report_model = Mock()
        report_model.get_type = Mock(return_value=Report)
        return PusherActor('pusher_test', report_model, fake_db, level_logger=logging.DEBUG, max_size=buffer_size,
                           delay=delay)

    @define_buffer_size(0)
    def test_send_one_report_to_pusher_with_0sized_buffer_make_it_save_the_report(self, started_actor, fake_db):
        started_actor.send_data(REPORT1)
        assert fake_db.q.get(timeout=1) == [REPORT1]

    @define_buffer_size(1)
    def test_send_one_report_to_pusher_with_1sized_buffer_make_it_not_save_the_report(self, started_actor, fake_db):
        started_actor.send_data(REPORT1)
        with pytest.raises(Empty):
            fake_db.q.get(timeout=1)

    @define_buffer_size(1)
    def test_send_two_report_to_pusher_with_1sized_buffer_make_it_save_the_reports_in_one_call(self, started_actor, fake_db):
        started_actor.send_data(REPORT1)
        started_actor.send_data(REPORT2)
        assert fake_db.q.get(timeout=1) == [REPORT1, REPORT2]

    @define_delay(0)
    def test_send_one_report_to_pusher_with_0delay_make_it_save_the_reports(self, started_actor, fake_db):
        started_actor.send_data(REPORT1)
        assert fake_db.q.get(timeout=1) == [REPORT1]

    @define_delay(2000)
    def test_send_two_report_to_pusher_with_2seconde_delay_make_it_not_save_the_reports(self, started_actor, fake_db):
        started_actor.send_data(REPORT1)
        started_actor.send_data(REPORT2)
        with pytest.raises(Empty):
            fake_db.q.get(timeout=1)

    @define_delay(2000)
    def test_send_two_report__with_two_second_between_messages_to_pusher_with_2seconde_delay_make_it_save_the_report(self, started_actor, fake_db):
        started_actor.send_data(REPORT1)
        time.sleep(2)
        started_actor.send_data(REPORT2)
        assert fake_db.q.get(timeout=1) == [REPORT1, REPORT2]

    @define_buffer_size(1)
    def test_send_two_report_in_wrong_time_order_to_a_pusher_make_it_save_them_in_good_order(self, started_actor, fake_db):
        started_actor.send_data(REPORT2)
        started_actor.send_data(REPORT1)
        assert fake_db.q.get(timeout=1) == [REPORT1, REPORT2]

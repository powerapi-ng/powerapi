# Copyright (c) 2018, INRIA
# Copyright (c) 2018, University of Lille
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
import logging

from multiprocessing import Queue

import pytest

from mock import Mock
from powerapi.report import Report
from powerapi.puller import PullerActor
from powerapi.message import StartMessage, ErrorMessage
from powerapi.filter import Filter

from ..actor.abstract_test_actor import AbstractTestActor
from ..db_utils import FakeDB, AbstractTestActorWithDB, define_database_content, REPORT1, REPORT2


def define_filter(filt):
    """
    Decorator to set the _filt
    attribute for individual tests.
    """
    def wrap(func):
        setattr(func, '_filter', filt)
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


    if 'filt' in metafunc.fixturenames:
        filt = getattr(metafunc.function, '_filter', None)
        metafunc.parametrize('filt', [filt])


class FakeDispatcher:

    def __init__(self):
        self.q = Queue()

    def send_data(self, report):
        self.q.put(report, block=False)


class TestPuller(AbstractTestActorWithDB):

    @pytest.fixture
    def fake_dispatcher(self):
        return FakeDispatcher()

    @pytest.fixture
    def fake_filter(self, fake_dispatcher):
        fake_filter = Mock()
        fake_filter.filters = [(Mock(return_value=True), Mock())]
        fake_filter.route = Mock(return_value=[fake_dispatcher])
        fake_filter.get_type = Mock(return_value=Report)
        return fake_filter

    @pytest.fixture
    def actor(self, fake_db, filt, fake_filter):
        filter = fake_filter if filt is None else filt
        return PullerActor('puller_test', fake_db, filter, 0, level_logger=logging.DEBUG)

    @define_database_content([REPORT1, REPORT2])
    def test_start_actor_with_db_thath_contains_2_report_make_actor_send_reports_to_dispatcher(self, started_actor, fake_dispatcher, content):
        for report in content:
            assert fake_dispatcher.q.get(timeout=2) == report

    def test_starting_actor_in_stream_mode_make_it_terminate_itself_after_empty_db(self, started_actor):
        started_actor.join(2)
        assert started_actor.is_alive() is False

    @define_filter(Filter())
    def test_send_start_message_to_puller_without_filter_answer_with_error_message(self, init_actor):
        init_actor.send_control(StartMessage())
        msg = init_actor.receive_control(2000)
        assert isinstance(msg, ErrorMessage)

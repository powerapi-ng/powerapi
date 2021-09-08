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
import logging
import time
from multiprocessing import Pipe

import pytest

from mock import Mock

from thespian.actors import ActorExitRequest

from powerapi.puller import PullerActor
from powerapi.message import PullerStartMessage, ErrorMessage, StartMessage, EndMessage
from powerapi.filter import Filter, RouterWithoutRuleException
from powerapi.report import Report
from powerapi.test_utils.abstract_test import AbstractTestActor, AbstractTestActorWithDB, define_database_content, recv_from_pipe
from powerapi.test_utils.db import FakeDB
from powerapi.test_utils.dummy_actor import DummyActor, DummyStartMessage
from powerapi.test_utils.actor import is_actor_alive, system

REPORT1 = Report(1, 2, 3)
REPORT2 = Report(3, 4, 5)


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


def filter_rule(report):
    return True

class TestPuller(AbstractTestActorWithDB):

    @pytest.fixture
    def fake_dispatcher(self, system, dummy_pipe_in):
        dispatcher = system.createActor(DummyActor)
        system.tell(dispatcher, DummyStartMessage('system', 'dispatcher', dummy_pipe_in))
        return dispatcher

    @pytest.fixture
    def fake_filter(self, fake_dispatcher):
        fake_filter = Filter()
        fake_filter.filter(filter_rule, fake_dispatcher)
        return fake_filter

    @pytest.fixture
    def empty_filter(self):
        fake_filter = Filter()
        return fake_filter

    @pytest.fixture
    def actor(self, system):
        puller = system.createActor(PullerActor)
        yield puller
        system.tell(puller, ActorExitRequest())

    @pytest.fixture
    def actor_start_message(self, system, actor, fake_db, fake_filter):
        return PullerStartMessage('system', 'puller_test', fake_db, fake_filter, False)

    def test_create_puller_with_router_without_rules_must_raise_RouterWithoutRuleException(self, system, empty_filter, fake_db):
        puller = system.createActor(PullerActor)
        puller_start_message = PullerStartMessage('system', 'puller_test', fake_db, empty_filter, False)
        answer = system.ask(puller, puller_start_message)
        assert isinstance(answer, ErrorMessage)
        assert answer.error_message == 'filter without rules'

    @define_database_content([REPORT1, REPORT2])
    def test_start_actor_with_db_that_contains_2_report_make_actor_send_reports_to_dispatcher(self, system, started_actor, fake_dispatcher, content, dummy_pipe_out):

        for report in content:
            assert recv_from_pipe(dummy_pipe_out, 2) == ('dispatcher', report)

    def test_starting_actor_in_non_stream_mode_make_it_terminate_itself_after_empty_db(self, system, started_actor):
        time.sleep(1)
        assert not is_actor_alive(system, started_actor)

    def test_starting_actor_in_non_stream_mode_make_it_send_EndMessage_after_empty_db(self, system, started_actor):
        time.sleep(1)
        assert(isinstance(system.listen(3), EndMessage))

    def test_starting_actor_in_non_stream_mode_make_it_send_EndMessage_to_dispatcher(self, system, started_actor, fake_filter, dummy_pipe_out):
        _, msg = recv_from_pipe(dummy_pipe_out, 2)
        assert isinstance(msg, EndMessage)

    def test_starting_actor_in_stream_mode_dont_terminate_itself_after_empty_db(self, system, actor, fake_db, fake_filter):
        assert is_actor_alive(system, actor)
        puller_start_message = PullerStartMessage('system', 'puller_test', fake_db, fake_filter, True)
        answer = system.ask(actor, puller_start_message)
        time.sleep(1)
        assert is_actor_alive(system, actor)

    def test_starting_actor_with_a_non_PullerStartMessage_must_answer_error_message(self, system, actor):
        puller_start_message = StartMessage('system', 'puller_test')
        answer = system.ask(actor, puller_start_message)
        assert isinstance(answer, ErrorMessage)
        assert answer.error_message == 'use PullerStartMessage instead of StartMessage'

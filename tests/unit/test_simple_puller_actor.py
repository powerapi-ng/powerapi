# Copyright (c) 2022, INRIA
# Copyright (c) 2022, University of Lille
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


import pytest

from thespian.actors import ActorExitRequest

from powerapi.message import ErrorMessage, StartMessage, SimplePullerStartMessage, \
    SimplePullerSendReportsMessage
from powerapi.filter import Filter
from powerapi.report import HWPCReport
from powerapi.simple_puller import SimplePullerActor
from powerapi.test_utils.abstract_test import AbstractTestActor, \
    recv_from_pipe

from powerapi.test_utils.dummy_actor import DummyActor, DummyStartMessage
from powerapi.test_utils.actor import is_actor_alive, system

NUMBER_OF_REPORTS_TO_SEND = 10
REPORT_TYPE_TO_BE_SENT = HWPCReport


def filter_rule(report):
    return True


class TestSimplePuller(AbstractTestActor):

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
        puller = system.createActor(SimplePullerActor)
        yield puller
        system.tell(puller, ActorExitRequest())

    @pytest.fixture
    def actor_start_message(self, system, actor, fake_filter):
        return SimplePullerStartMessage(sender_name='system', name='simple_puller_test',
                                        number_of_reports_to_send=NUMBER_OF_REPORTS_TO_SEND,
                                        report_type_to_send=REPORT_TYPE_TO_BE_SENT,
                                        report_filter=fake_filter)

    def test_create_simple_puller_with_router_without_rules_must_raise_RouterWithoutRuleException(self, system,
                                                                                                  empty_filter):
        simple_puller = system.createActor(SimplePullerActor)
        simple_puller_start_message = SimplePullerStartMessage(sender_name='system', name='simple_puller_test',
                                                               number_of_reports_to_send=NUMBER_OF_REPORTS_TO_SEND,
                                                               report_type_to_send=REPORT_TYPE_TO_BE_SENT,
                                                               report_filter=empty_filter)
        answer = system.ask(simple_puller, simple_puller_start_message)
        assert isinstance(answer, ErrorMessage)
        assert answer.error_message == 'filter without rules'

    # @define_database_content([REPORT1, REPORT2])
    def test_start_actor_send_reports_to_dispatcher(self, system,
                                                    started_actor,
                                                    fake_dispatcher,
                                                    dummy_pipe_out):
        count = 0
        report = REPORT_TYPE_TO_BE_SENT.create_empty_report()
        system.tell(started_actor, SimplePullerSendReportsMessage('system', 'simple_puller_test'))
        while count < NUMBER_OF_REPORTS_TO_SEND:
            assert recv_from_pipe(dummy_pipe_out, 2) == ('dispatcher', report)
            count += 1

    def test_starting_actor_terminate_itself_after_ActorExitRequest_reception(self, system, started_actor):
        system.tell(started_actor, ActorExitRequest())
        assert not is_actor_alive(system, started_actor)

    def test_starting_actor_with_a_no_SimplePullerStartMessage_must_answer_error_message(self, system, actor):
        puller_start_message = StartMessage('system', 'puller_test')
        answer = system.ask(actor, puller_start_message)
        assert isinstance(answer, ErrorMessage)
        assert answer.error_message == 'use SimplePullerStartMessage instead of StartMessage'

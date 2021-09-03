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
import pytest

from thespian.actors import ActorAddress

from powerapi.supervisor import Supervisor
from powerapi.message import PullerStartMessage, PusherStartMessage, DispatcherStartMessage, StartMessage, PingMessage, OKMessage
from powerapi.puller import PullerActor
from powerapi.pusher import PusherActor
from powerapi.dispatcher import DispatcherActor, RouteTable
from powerapi.filter import Filter
from powerapi.actor import InitializationException
from powerapi.dispatch_rule import DispatchRule
from powerapi.report import Report

from powerapi.test_utils.actor import system, puller_start_message, pusher_start_message, dispatcher_start_message
from powerapi.test_utils.dummy_actor import CrashInitActor
from powerapi.test_utils.db import SilentFakeDB

VERBOSE_MODE=True

@pytest.fixture
def supervisor(system):
    return Supervisor(VERBOSE_MODE)


def rule(r):
    return True


@pytest.mark.timeout(3)
def test_monitor_a_puller_actor_in_non_stream_mode_with_an_empty_database_must_return(system, supervisor):
    filter = Filter()
    filter.filter(rule, None)
    supervisor.launch(PullerActor, PullerStartMessage('system', 'test_puller', SilentFakeDB(), filter, False))
    supervisor.monitor()


class BaseSupervisorTest:

    def test_launch_an_actor_with_supervisor_return_ActorAddress(self, supervisor, actor_cls, start_message):
        actor = supervisor.launch(actor_cls, start_message)
        assert isinstance(actor, ActorAddress)


    def test_launch_an_actor_with_supervisor_and_send_it_a_PingMessage_must_answer_with_OKMessage(self, system, supervisor, actor_cls, start_message):
        actor = supervisor.launch(actor_cls, start_message)
        isinstance(system.ask(actor, PingMessage('system')), OKMessage)

@pytest.fixture
def database():
    return SilentFakeDB()

@pytest.fixture
def report_type():
    return Report

    
class TestSupervisorWithPuller(BaseSupervisorTest):
    @pytest.fixture
    def actor_cls(self):
        return PullerActor

    @pytest.fixture
    def stream_mode(self):
        return False

    @pytest.fixture
    def report_filter(self):
        filter = Filter()
        filter.filter(rule, None)
        return filter

    @pytest.fixture
    def start_message(self, puller_start_message):
        return puller_start_message


class TestSupervisorWithPusher(BaseSupervisorTest):
    @pytest.fixture
    def actor_cls(self):
        return PusherActor
    @pytest.fixture
    def start_message(self, pusher_start_message):
        return pusher_start_message


class TestSupervisorWithDispatcher(BaseSupervisorTest):
    @pytest.fixture
    def actor_cls(self):
        return DispatcherActor
    @pytest.fixture
    def formula_class(self):
        return None
    @pytest.fixture
    def formula_values(self):
        return None
    @pytest.fixture
    def route_table(self, report_type):
        route_table = RouteTable()
        route_table.dispatch_rule(type(report_type), DispatchRule(primary=True))
        return route_table
    @pytest.fixture
    def start_message(self, dispatcher_start_message):
        return dispatcher_start_message

def test_launch_an_actor_that_crash_at_initialization_must_raise_InitiliasationError(supervisor):
    with pytest.raises(InitializationException):
        supervisor.launch(CrashInitActor, StartMessage('system', 'test'))

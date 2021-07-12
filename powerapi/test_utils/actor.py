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

from thespian.actors import ActorSystem, ActorExitRequest, ActorAddress

from powerapi.report import Report
from powerapi.pusher import PusherActor
from powerapi.puller import PullerActor
from powerapi.dispatcher import DispatcherActor
from powerapi.formula import FormulaActor
from powerapi.message import PusherStartMessage, PullerStartMessage, DispatcherStartMessage, FormulaStartMessage
from powerapi.message import PingMessage, StartMessage, OKMessage


PUSHER_NAME = 'test_pusher'
PULLER_NAME = 'test_puller'
DISPATCHER_NAME = 'test_dispatcher'
DISPATCHER_DEVICE_ID = 'test_device'

@pytest.fixture
def system():
    syst = ActorSystem(systemBase='multiprocQueueBase')
    yield syst
    syst.shutdown()

@pytest.fixture
def shutdown_system():
    yield None
    syst = ActorSystem(systemBase='multiprocQueueBase')
    syst.shutdown()


@pytest.fixture()
def puller(system):
    actor = system.createActor(PullerActor)
    yield actor
    system.tell(actor, ActorExitRequest())


@pytest.fixture()
def puller_start_message(database, report_filter, report_model, stream_mode):
    return PullerStartMessage('system', PULLER_NAME, database, report_filter, report_model, stream_mode)


@pytest.fixture()
def started_puller(system, puller, puller_start_message):
    system.ask(puller, puller_start_message)
    return puller


@pytest.fixture()
def pusher(system):
    actor = system.createActor(PusherActor)
    yield actor
    system.tell(actor, ActorExitRequest())


@pytest.fixture()
def pusher_start_message(database, report_model):
    return PusherStartMessage('system', PUSHER_NAME, database, report_model)


@pytest.fixture()
def started_pusher(system, pusher, pusher_start_message):
    system.ask(pusher, pusher_start_message)
    return pusher

@pytest.fixture()
def dispatcher(system):
    actor = system.createActor(DispatcherActor)
    yield actor
    system.tell(actor, ActorExitRequest())


@pytest.fixture()
def dispatcher_start_message(formula_class, formula_values, route_table):
    return DispatcherStartMessage('system', DISPATCHER_NAME, formula_class, formula_values, route_table, DISPATCHER_DEVICE_ID)

@pytest.fixture()
def started_dispatcher(system, dispatcher, dispatcher_start_message):
    system.ask(dispatcher, dispatcher_start_message)
    return dispatcher


class CrashFormula(FormulaActor):
    """
    Formula that crash when receiving a report
    """
    def __init__(self):
        FormulaActor.__init__(self, FormulaStartMessage)

    def receiveMsg_Report(self, message: Report, sender: ActorAddress):
        raise Exception()


def is_actor_alive(system, actor_address, time=1):
    """
    wait the actor to terminate or 0.5 secondes and return its is_alive value
    """
    msg = system.ask(actor_address, PingMessage('system'), time)
    print(msg)
    return isinstance(msg, OKMessage)

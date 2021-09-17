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
import pytest

from thespian.actors import ActorSystem, ActorExitRequest, ActorAddress

from powerapi.report import Report
from powerapi.pusher import PusherActor
from powerapi.puller import PullerActor
from powerapi.dispatcher import DispatcherActor
from powerapi.formula import FormulaActor
from powerapi.message import PusherStartMessage, PullerStartMessage, DispatcherStartMessage, FormulaStartMessage
from powerapi.message import PingMessage, OKMessage
from powerapi.supervisor import LOG_DEF


PUSHER_NAME = 'test_pusher'
PULLER_NAME = 'test_puller'
DISPATCHER_NAME = 'test_dispatcher'
DISPATCHER_DEVICE_ID = 'test_device'


@pytest.fixture
def system():
    """
    fixture that start an Actor system with log enabled before launching the test and shutdown it after the test end
    """
    syst = ActorSystem(systemBase='multiprocQueueBase', logDefs=LOG_DEF)
    yield syst
    syst.shutdown()


@pytest.fixture
def shutdown_system():
    """
    fixture that shutdown all multiproQeueuBase actor system after the test end
    """
    yield None
    syst = ActorSystem(systemBase='multiprocQueueBase', logDefs=LOG_DEF)
    syst.shutdown()


@pytest.fixture()
def puller(system):
    """
    fixture that create a PullerActor before launching the test and stop it after the test end
    """
    actor = system.createActor(PullerActor)
    yield actor
    system.tell(actor, ActorExitRequest())


@pytest.fixture()
def puller_start_message(database, report_filter, stream_mode):
    """
    return a puller start message
    """
    return PullerStartMessage('system', PULLER_NAME, database, report_filter, stream_mode)


@pytest.fixture()
def started_puller(system, puller, puller_start_message):
    """
    fixture that create and start a PullerActor and actor before launching the test and stop it after the test end
    """
    system.ask(puller, puller_start_message)
    return puller


@pytest.fixture()
def pusher(system):
    """
    fixture that create a PusherActor before launching the test and stop it after the test end
    """
    actor = system.createActor(PusherActor)
    yield actor
    system.tell(actor, ActorExitRequest())


@pytest.fixture()
def pusher_start_message(database):
    """
    return a pusher start message
    """
    return PusherStartMessage('system', PUSHER_NAME, database)


@pytest.fixture()
def started_pusher(system, pusher, pusher_start_message):
    """
    fixture that create and start a PusherActor and actor before launching the test and stop it after the test end
    """
    system.ask(pusher, pusher_start_message)
    return pusher


@pytest.fixture()
def dispatcher(system):
    """
    fixture that create a DispatcherActor before launching the test and stop it after the test end
    """
    actor = system.createActor(DispatcherActor)
    yield actor
    system.tell(actor, ActorExitRequest())


@pytest.fixture()
def dispatcher_start_message(formula_class, formula_values, route_table):
    """
    return a dispatcher start message
    """
    return DispatcherStartMessage('system', DISPATCHER_NAME, formula_class, formula_values, route_table, DISPATCHER_DEVICE_ID)


@pytest.fixture()
def started_dispatcher(system, dispatcher, dispatcher_start_message):
    """
    fixture that create and start a DispatcherActor and actor before launching the test and stop it after the test end
    """
    system.ask(dispatcher, dispatcher_start_message)
    return dispatcher


class CrashFormula(FormulaActor):
    """
    Formula that crash when receiving a report
    """
    def __init__(self):
        FormulaActor.__init__(self, FormulaStartMessage)

    @staticmethod
    def receiveMsg_Report(message: Report, sender: ActorAddress):
        """
        crash when receiving a report
        """
        raise Exception()


def is_actor_alive(system, actor_address, time=1):
    """
    wait the actor to terminate or 0.5 secondes and return its is_alive value
    """
    msg = system.ask(actor_address, PingMessage('system'), time)
    return isinstance(msg, OKMessage)

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
import logging

import pytest

from powerapi.actor.actor import InitializationException
from powerapi.handler import PoisonPillMessageHandler, StartHandler
from powerapi.message import StartMessage, Message, PoisonPillMessage
from powerapi.actor import Actor as PowerapiActor, Actor, State
from powerapi.formula import DomainValues
from powerapi.test_utils.dummy_handlers import DummyHandler, DummyFormulaHandler, CrashFormulaHandler, \
    CrashInitFormulaHandler

LOGGER_NAME = 'multiprocess_test_logger'


class DummyActorState(State):
    """
    Message used to start a DummyActor
    :param pipe: pipe used to send message to pytest process
    """

    def __init__(self, actor: Actor, pipe):
        State.__init__(self, actor)
        self.pipe = pipe


class DummyActor(Actor):
    """
    Actor that forward all start message (except StartMessage) into a pipe to the test process
    """

    def __init__(self, name: str, pipe, message_type):
        Actor.__init__(self, name)
        self.state = DummyActorState(self, pipe)
        self.message_type = message_type

    def setup(self):
        """
        Define message handler
        """
        self.add_handler(self.message_type, DummyHandler(self.state))
        self.add_handler(PoisonPillMessage, PoisonPillMessageHandler(self.state))
        self.add_handler(StartMessage, StartHandler(self.state))
        print('setup: Called in '+str(self))


class DummyFormulaActorState(State):
    """
    Message used to start a DummyActor
    :param pipe: pipe used to send message to pytest process
    """

    def __init__(self, actor: Actor, fake_pusher: Actor):
        State.__init__(self, actor)
        self.fake_pusher = fake_pusher


class DummyFormulaActor(Actor):
    """
    A fake FormulaActor that is connected to a DummyActor (a fake pusher)
    """

    def __init__(self, name: str, fake_pusher: Actor):
        Actor.__init__(self, name)
        self.state = DummyFormulaActorState(self, fake_pusher)

    def setup(self):
        """
        Define message handler
        """
        self.add_handler(Message, DummyFormulaHandler(self.state))

    @staticmethod
    def gen_domain_values(device_id, formula_id):
        return DomainValues(device_id, formula_id)


class CrashFormulaActor(DummyFormulaActor):
    """
    Formula that crash after receiving 3 messages
    """

    def __init__(self, name: str, fake_pusher: Actor):
        DummyFormulaActor.__init__(self, name, fake_pusher)
        self.report_received = 0

    def setup(self):
        """
        Define message handler
        """
        self.add_handler(Message, CrashFormulaHandler(self.state))


class CrashInitFormulaActor(DummyFormulaActor):
    """
    Formula answer ErrorMessage to StartMessage
    Like DummyFormulaActor, it will forward received Message to fake pusher
    """

    def __init__(self, name: str, fake_pusher: Actor):
        DummyFormulaActor.__init__(self, name, fake_pusher)

    def setup(self):
        """
        Define message handler
        """
        self.add_handler(Message, CrashInitFormulaHandler(self.state))


class DummyPowerapiActor(PowerapiActor):
    """
    Actor that have the same API than a basic powerapi actor
    """

    def __init__(self, name: str):
        PowerapiActor.__init__(self, name)


class CrashInitActor(DummyPowerapiActor):
    """
    Basic powerapi actor that crash at setup
    """

    def setup(self, msg):
        raise InitializationException('error')

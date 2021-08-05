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

import pytest

from thespian.actors import Actor, ActorSystem, ActorExitRequest

from powerapi.message import PingMessage, StartMessage, OKMessage, ErrorMessage
from powerapi.actor import Actor as PowerapiActor, InitializationException
from powerapi.formula import DomainValues

LOGGER_NAME='thespian_test_logger'

@pytest.fixture
def logger(system, dummy_pipe_in):
    logger_actor = system.createActor(DummyActor, globalName=LOGGER_NAME)
    system.tell(logger_actor, DummyStartMessage('system', 'logger', dummy_pipe_in))
    yield logger_actor
    system.tell(logger_actor, ActorExitRequest())


class DummyStartMessage(StartMessage):
    def __init__(self, sender_name, name, pipe):
        StartMessage.__init__(self, sender_name, name)
        self.pipe = pipe


class DummyActor(Actor):
    """
    Actor that forward all start message (except StartMessage) into a pipe to the test process
    """
    def __init__(self):
        Actor.__init__(self)
        self.pipe = None


    def receiveMessage(self, message, sender):
        if isinstance(message, DummyStartMessage):
            self.pipe = message.pipe
            self.name = message.name
        else:
            self.pipe.send((self.name, message))
            logging.debug('receive : ' + str(message), extra={'actor_name': self.name})


class DummyFormulaActor(Actor):
    """
    Formula that forward received message to fake pusher
    """
    def __init__(self):
        self.name = None
        self.fake_puller = None

    def receiveMessage(self, message, sender):
        logging.debug('receive : ' + str(message), extra={'actor_name': self.name})
        if isinstance(message, StartMessage):
            self.name = message.name
            self.fake_puller = self.createActor(DummyActor, globalName=message.values.pushers['fake_pusher'])
            self.send(self.fake_puller, message)
            self.send(sender, OKMessage(self.name))
        elif isinstance(message, ActorExitRequest):
            self.send(self.fake_puller, 'dead')
        else:
            self.send(self.fake_puller, message)

    @staticmethod
    def gen_domain_values(device_id, formula_id):
        return DomainValues(device_id, formula_id)


class CrashException(Exception):
    pass


class CrashFormulaActor(DummyFormulaActor):
    """
    Formula that crash after receiving 3 messages
    """
    def __init__(self):
        DummyFormulaActor.__init__(self)
        self.report_received = 0

    
        
    def receiveMessage(self, message, sender):
        logging.debug('receive : ' + str(message), extra={'actor_name': self.name})
        if isinstance(message, StartMessage):
            self.name = message.name
            self.fake_puller = self.createActor(DummyActor, globalName=message.values.pushers['fake_pusher'])
            self.send(self.fake_puller, message)
            self.send(sender, OKMessage(self.name))
        elif isinstance(message, ActorExitRequest):
            self.send(self.fake_puller, 'dead')
        else:
            self.report_received += 1
            if self.report_received >= 3:
                self.send(self.fake_puller, 'crash')
                raise CrashException
            self.send(self.fake_puller, message)


class CrashInitFormulaActor(DummyFormulaActor):
    """
    Formula that at initialization end answer ErrorMessage to StartMessage
    Like DummyFormulaActor, it will forward received Message to fake pusher
    """
    def __init__(self):
        DummyFormulaActor.__init__(self)
        self.report_received = 0

    def receiveMessage(self, message, sender):
        if isinstance(message, StartMessage):
            self.name = message.name
            self.fake_puller = self.createActor(DummyActor, globalName=message.values.pushers['fake_pusher'])
            self.send(sender, ErrorMessage(self.name, 'formula crashed'))
        elif isinstance(message, ActorExitRequest):
            self.send(self.fake_puller, 'dead')
        else:
            self.send(self.fake_puller, message)


class DummyPowerapiActor(PowerapiActor):
    """
    Actor that have the same thant a basic powerapi actor
    """

    def __init__(self):
        PowerapiActor.__init__(self, StartMessage)


class CrashInitActor(DummyPowerapiActor):
    """
    Basic powerapi actor that crash a initialisation
    """
    def _initialization(self, msg):
        raise InitializationException('error')


class CrashActor(DummyPowerapiActor):
    """
    Basic powerapi actor that crash after 2s
    """
    def _initialization(self, msg):
        self.wakeupAfter(2)

    def receiveMsg_WakeupMessage(self, message, sender):
        raise CrashException()

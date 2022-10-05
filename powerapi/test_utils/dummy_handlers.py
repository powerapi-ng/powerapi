# Copyright (c) 2018, INRIA
# Copyright (c) 2018, University of Lille
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

from powerapi.actor import State
from powerapi.handler import Handler
from powerapi.message import EndMessage, Message, StartMessage, ErrorMessage


class DummyHandler(Handler):

    def __init__(self, state):
        Handler.__init__(self, state)

    def handle(self, msg: Message):
        """
        Handle a message and return a new state value of the actor

        :param Object msg: the message received by the actor
        """
        print('DummyHandler: receive '+str(msg))
        self.state.pipe.send((self.state.actor.name, msg))
        print('DummyHandler: sent ' + str(msg))
        logging.debug('receive : ' + str(msg), extra={'actor_name': self.state.actor.name})


class DummyFormulaHandler(Handler):

    def __init__(self, state: State):
        Handler.__init__(self, state)

    def handle(self, msg: Message):
        """
        When receiving a message :
        if its an ActorExitRequest : notify the pusher that the Dummyformula died
        if its an other type of message : forward it to the fake puller
        """
        print('DummyFormulaHandler: receive: '+str(msg))
        logging.debug('receive : ' + str(msg), extra={'actor_name': self.state.actor.name})

        if isinstance(msg, EndMessage):
            self.state.fake_pusher.send_control(msg)
        else:
            print('DummyFormulaHandler: sending to fake_pusher '+str(self.state.fake_pusher)+ ' message ' + str(msg))
            self.state.fake_pusher.send_data(msg)
            print('DummyFormulaHandler: sent to fake_pusher ' + str(msg))


class CrashException(Exception):
    """
    Exception raised by formla to make it crash
    """


class CrashFormulaHandler(DummyFormulaHandler):

    def __init__(self, state: State):
        DummyFormulaHandler.__init__(self, state)

    def handle(self, msg: Message):
        """
        When receiving a message :
        if its an ActorExitRequest : notify the pusher that the Dummyformula died
        if its an other type of message : forward it to the fake puller
        """
        logging.debug('receive : ' + str(msg), extra={'actor_name': self.state.actor.name})
        self.state.actor.report_received += 1

        if self.report_received >= 3:
            self.state.fake_puller.send_control(EndMessage(self.state.fake_puller.name))
            raise CrashException

        super().handle(msg)


class CrashInitFormulaHandler(DummyFormulaHandler):

    def __init__(self, state: State):
        DummyFormulaHandler.__init__(self, state)

    def handle(self, msg: Message):
        """
        When receiving a message :
        if its an ActorExitRequest : notify the pusher that the Dummyformula died
        if its an other type of message : forward it to the fake puller
        """
        logging.debug('receive : ' + str(msg), extra={'actor_name': self.state.actor.name})

        if isinstance(msg, StartMessage):
            self.state.fake_pusher.send_control(ErrorMessage(self.state.actor.name, 'formula crashed'))
        else:
            super().handle(msg)

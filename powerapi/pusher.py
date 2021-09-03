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
from thespian.actors import ActorAddress, ActorExitRequest

from powerapi.actor import Actor, InitializationException
from powerapi.message import PusherStartMessage, EndMessage
from powerapi.database import DBError
from powerapi.report import PowerReport


class PusherActor(Actor):
    """
    PusherActor class

    The Pusher allow to save Report sent by Formula.
    """

    def __init__(self):
        Actor.__init__(self, PusherStartMessage)
        self.database = None

    def _initialization(self, start_message: PusherStartMessage):
        Actor._initialization(self, start_message)
        self.database = start_message.database

        try:
            self.database.connect()
        except DBError as error:
            raise InitializationException(error.msg) from error

    def receiveMsg_PowerReport(self, message: PowerReport, _: ActorAddress):
        """
        When receiving a PowerReport save it to database
        """
        self.log_debug('received message ' + str(message))
        self.database.save(message)

    def receiveMsg_EndMessage(self, message: EndMessage, _: ActorAddress):
        """
        When receiving an EndMessage notify the ActorSystem and Kill itself
        """
        self.log_debug('received message ' + str(message))
        self.send(self.parent, EndMessage(self.name))
        self.send(self.myAddress, ActorExitRequest())

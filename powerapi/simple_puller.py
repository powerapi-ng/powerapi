# Copyright (c) 2022, INRIA
# Copyright (c) 2022, University of Lille
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
from powerapi.message import SimplePullerStartMessage, StartMessage, EndMessage, ErrorMessage, \
    SimplePullerSendReportsMessage


class SimplePullerActor(Actor):
    """
    Simple Actor that generated a given number of messages of the giver type
    """

    def __init__(self):
        Actor.__init__(self, SimplePullerStartMessage)

        self.number_of_reports_to_send = 0
        self.report_type_to_send = None
        self.report_filter = None

    def _initialization(self, start_message: SimplePullerStartMessage):
        self.number_of_reports_to_send = start_message.number_of_reports_to_send
        self.report_type_to_send = start_message.report_type_to_send
        self.report_filter = start_message.report_filter

        if not self.report_filter.filters:
            raise InitializationException('filter without rules')

        if self.report_type_to_send is None:
            raise InitializationException('The report type to be sent has to be defined')

    def receiveMsg_StartMessage(self, message: StartMessage, sender: ActorAddress):
        Actor.receiveMsg_StartMessage(self, message=message, sender=sender)

    def receiveMsg_SimplePullerSendReportsMessage(self, _: SimplePullerSendReportsMessage, __: ActorAddress):

        sent = 0
        while sent < self.number_of_reports_to_send:
            report = self.report_type_to_send.create_empty_report()
            dispatchers = self.report_filter.route(report)
            for dispatcher in dispatchers:
                self.log_debug('send report ' + str(report) + 'to ' + str(dispatcher))
                self.send(dispatcher, report)
            sent += 1

    def receiveMsg_ActorExitRequest(self, message: ActorExitRequest, _: ActorAddress):
        """
        When receive ActorExitRequestMessage log it and exit
        """
        Actor.receiveMsg_ActorExitRequest(self, message, _)
        self.send(self.parent, EndMessage(self.name))

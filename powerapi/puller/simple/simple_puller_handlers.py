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

from powerapi.actor import State
from powerapi.handler import Handler, StartHandler
from powerapi.message import Message, SimplePullerSendReportsMessage
from powerapi.exception import UnknownMessageTypeException
from powerapi.puller.handlers import PullerInitializationException


class SimplePullerStartHandler(StartHandler):
    """
    Initialize the database interface
    """

    def __init__(self, state: State):
        StartHandler.__init__(self, state)

    def initialization(self):
        if self.state.report_filter.filters is None or len(self.state.report_filter.filters) == 0:
            raise PullerInitializationException('No filters')
        # Connect to all dispatcher
        for _, dispatcher in self.state.report_filter.filters:
            dispatcher.connect_data()


class SimplePullerHandler(Handler):
    """
    Initialize the database interface
    """

    def __init__(self, state: State):
        Handler.__init__(self, state)

    def handle(self, msg: Message):
        """
        The reception of a SimplePullerSendReportsMessage makes actor to send x messages to the dispatcher
        """
        if isinstance(msg, SimplePullerSendReportsMessage):
            sent = 0
            while sent < self.state.number_of_reports_to_send:
                report = self.state.report_type_to_send.create_empty_report()
                dispatchers = self.state.report_filter.route(report)
                for dispatcher in dispatchers:
                    self.state.actor.logger.debug('send report ' + str(report) + ' to ' + str(dispatcher))
                    dispatcher.send_data(report)
                sent += 1
            self.state.actor.logger.debug('sent reports: ' + str(sent))
        else:
            raise UnknownMessageTypeException()

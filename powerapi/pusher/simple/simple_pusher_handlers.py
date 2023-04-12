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
from powerapi.message import Message, PoisonPillMessage, \
    GetReceivedReportsSimplePusherMessage, ReceivedReportsSimplePusherMessage
from powerapi.report import Report


class SimplePusherStartHandler(StartHandler):
    """
    Initialize the database interface
    """

    def __init__(self, state: State):
        StartHandler.__init__(self, state)

    def initialization(self):
        pass


class SimplePusherHandler(Handler):
    """
    Initialize the database interface
    """

    def __init__(self, state: State):
        Handler.__init__(self, state)

    def handle(self, report: Report):
        """
        The reception of a Report makes actor to store it and stop itself if required
        """
        # When receiving a Report save it to the list of reports
        self.state.actor.logger.debug('received message ' + str(report))
        self.save_report(report)
        self.state.actor.logger.debug(str(report) + ' saved to list')
        self.state.actor.logger.debug("reports saved :" + str(len(self.state.reports)))
        self.stop_actor_if_required()

    def save_report(self, report: Report):
        """
        Saves the received report in a list
        :param report: Report to be saved
        """
        self.state.reports.append(report)

    def stop_actor_if_required(self):
        """
        Stops the actor system if number_of_reports_to_store is reached
        """
        if len(self.state.reports) >= self.state.number_of_reports_to_store:
            self.state.actor.logger.debug("reports saved :" + str(len(self.state.reports)))
            self.state.actor.send_control(PoisonPillMessage(sender_name='system'))
            self.state.alive = 0
            self.state.actor.logger.debug("exit request sent")


class SimplePusherGetReceivedReportsHandler(Handler):
    """
    Handler for GetReceivedReports
    """
    def __init__(self, state: State):
        Handler.__init__(self, state)

    def handle(self, msg: Message):
        if isinstance(msg, GetReceivedReportsSimplePusherMessage):
            self.state.actor.send_control(ReceivedReportsSimplePusherMessage(self.state.actor.name, self.state.reports))

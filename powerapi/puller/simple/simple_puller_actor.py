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
import logging
from typing import Type

from powerapi.actor import Actor, State
from powerapi.message import StartMessage, \
    SimplePullerSendReportsMessage, PoisonPillMessage
from powerapi.puller import PullerPoisonPillMessageHandler
from powerapi.puller.simple.simple_puller_handlers import SimplePullerHandler, SimplePullerStartHandler
from powerapi.report import Report


class SimplePullerState(State):
    """
    Simple Puller Actor State

    Contains in addition to State values :
      - the number of reports to send
      - the report type to send
      - the report filter
    """

    def __init__(self, actor, number_of_reports_to_send: int, report_type_to_send: Type[Report], report_filter):
        """
        :param Actor actor: The actor related to the state
        :param int number_of_reports_to_send: Number of reports to send
        :param Report report_type_to_send: Report type to be sent
        :param Filter report_filter: Filters and the associated dispatchers and rules
        """
        State.__init__(self, actor)
        self.number_of_reports_to_send = number_of_reports_to_send
        self.report_type_to_send = report_type_to_send
        self.report_filter = report_filter


class SimplePullerActor(Actor):
    """
    Simple Actor that generated a given number of messages of a given type
    """

    def __init__(self, name: str, number_of_reports_to_send: int, report_type_to_send: Type[Report], report_filter,
                 level_logger: int = logging.WARNING):
        """
        Create an actor with the given information
        :param str name: The actor's name
        :param int number_of_reports_to_send: Number of reports to send
        :param Report report_type_to_send: Report type to be sent
        :param Filter report_filter: Filters and the associated dispatchers and rules
        """
        Actor.__init__(self, name, level_logger=level_logger)
        self.state = SimplePullerState(self, number_of_reports_to_send, report_type_to_send, report_filter)

    def setup(self):
        """
        Defines StartMessage handler, PoisonPillMessage handler and SimplePullerSendReportsMessage handler
        """
        self.add_handler(StartMessage, SimplePullerStartHandler(self.state))
        self.add_handler(PoisonPillMessage, PullerPoisonPillMessageHandler(self.state))
        self.add_handler(SimplePullerSendReportsMessage, SimplePullerHandler(self.state))

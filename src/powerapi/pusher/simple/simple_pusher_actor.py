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

from multiprocessing import Value

from powerapi.actor import Actor, State
from powerapi.handler import PoisonPillMessageHandler
from powerapi.message import StartMessage, \
    GetReceivedReportsSimplePusherMessage, PoisonPillMessage
from powerapi.pusher.simple.simple_pusher_handlers import SimplePusherStartHandler, SimplePusherHandler, \
    SimplePusherGetReceivedReportsHandler
from powerapi.report import PowerReport, HWPCReport


class SimplePusherState(State):
    """
        Simple Pusher Actor State

        Contains in addition to State values :
          - the number of reports to be stored
        """

    def __init__(self, actor, number_of_reports_to_store: int):
        """
        :param Actor actor: The actor related to the state
        :param int number_of_reports_to_store: Number of reports to store
        """
        State.__init__(self, actor)
        self.number_of_reports_to_store = number_of_reports_to_store
        self.reports = []
        self.alive = Value('i', 1)


class SimplePusherActor(Actor):
    """
    PusherActor class

    The Pusher allows to save Report sent by Formula.
    """

    def __init__(self, name: str, number_of_reports_to_store: int, level_logger: int = logging.WARNING):
        Actor.__init__(self, name=name, level_logger=level_logger)
        self.state = SimplePusherState(self, number_of_reports_to_store)

    def setup(self):
        """
        Defines StartMessage handler, PoisonPillMessage handler, PowerReport handler and HWPCReport handler
        """
        self.add_handler(StartMessage, SimplePusherStartHandler(self.state))
        self.add_handler(PoisonPillMessage, PoisonPillMessageHandler(self.state))
        report_handler = SimplePusherHandler(self.state)
        self.add_handler(PowerReport, report_handler)
        self.add_handler(HWPCReport, report_handler)
        self.add_handler(GetReceivedReportsSimplePusherMessage, SimplePusherGetReceivedReportsHandler(self.state))

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
from powerapi.actor import Actor, State
from powerapi.exception import PowerAPIException
from powerapi.message import PoisonPillMessage, StartMessage
from powerapi.puller import PullerPoisonPillMessageHandler
from powerapi.puller import PullerStartHandler
from powerapi.actor import NotConnectedException


class NoReportExtractedException(PowerAPIException):
    """
    Exception raised when we can't extract a report from the given
    database
    """


class PullerState(State):
    """
    Puller Actor State

    Contains in addition to State values :
      - the database interface
      - the Filter class
    """
    def __init__(self, actor, database, report_filter, report_model, stream_mode, timeout_puller):
        """
        :param BaseDB database: Allow to interact with a Database
        :param Filter report_filter: Filter of the Puller
        """
        super().__init__(actor)

        #: (BaseDB): Allow to interact with a Database
        self.database = database

        #: (it BaseDB): Allow to browse the database
        self.database_it = None

        #: (Filter): Filter of the puller
        self.report_filter = report_filter

        #: (ReportModel): ReportModel
        self.report_model = report_model

        #: (bool): Stream mode
        self.stream_mode = stream_mode

        #: (require stream mode = True) time (in ms) between two database reading
        self.timeout_puller = timeout_puller

        #: (int): Counter for "sleeping mode"
        self.counter = 0


class PullerActor(Actor):
    """
    PullerActor class

    A Puller allow to handle the reading of a database and to dispatch report
    to many Dispatcher depending of some rules.
    """

    def __init__(self, name, database, report_filter, report_model, stream_mode=False, level_logger=logging.WARNING,
                 timeout=0, timeout_puller=100):
        """
        :param str name: Actor name.
        :param BaseDB database: Allow to interact with a Database.
        :param Filter report_filter: Filter of the Puller.
        :param int level_logger: Define the level of the logger
        :param int tiemout_puller: (require stream mode) time (in ms) between two database reading
        """

        Actor.__init__(self, name, level_logger, timeout)
        #: (State): Actor State.
        self.state = PullerState(self, database, report_filter, report_model, stream_mode, timeout_puller)

    def setup(self):
        """
        Define StartMessage handler and PoisonPillMessage handler
        """
        self.add_handler(PoisonPillMessage, PullerPoisonPillMessageHandler(self.state))
        self.add_handler(StartMessage, PullerStartHandler(self.state, 0.1))

"""
Copyright (c) 2018, INRIA
Copyright (c) 2018, University of Lille
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import logging
from powerapi.actor import Actor, State, SocketInterface
from powerapi.message import PoisonPillMessage, StartMessage
from powerapi.handler import PoisonPillMessageHandler
from powerapi.puller import PullerStartHandler, TimeoutHandler
from powerapi.actor import NotConnectedException


class NoReportExtractedException(Exception):
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
    def __init__(self, behaviour, socket_interface, logger,
                 database, report_filter,
                 timeout_basic=0, timeout_sleeping=100):
        """
        :param func behaviour: Function that define the initial_behaviour
        :param SocketInterface socket_interface: Communication interface of the
                                                 actor
        :param BaseDB database: Allow to interact with a Database
        :param Filter report_filter: Filter of the Puller
        :param bool stream_mode: Puller stream_mode database.
        """
        State.__init__(self, behaviour, socket_interface, logger)

        #: (BaseDB): Allow to interact with a Database
        self.database = database

        #: (it BaseDB): Allow to browse the database
        self.database_it = None

        #: (Filter): Filter of the puller
        self.report_filter = report_filter

        #: (bool): Puller stream_mode database.
        self.stream_mode = database.stream_mode

        #: (int): Timeout for "basic mode"
        self.timeout_basic = timeout_basic

        #: (int): Timeout for "sleeping mode" (allow to free the CPU)
        self.timeout_sleeping = timeout_sleeping

        #: (int): Counter for "sleeping mode"
        self.counter = 0


class PullerActor(Actor):
    """
    PullerActor class

    A Puller allow to handle the reading of a database and to dispatch report
    to many Dispatcher depending of some rules.
    """

    def __init__(self, name, database, report_filter,
                 level_logger=logging.WARNING, timeout=0, timeout_sleeping=100):
        """
        :param str name: Actor name.
        :param BaseDB database: Allow to interact with a Database.
        :param Filter report_filter: Filter of the Puller.
        :param int level_logger: Define the level of the logger
        :param bool stream_mode: Puller stream_mode himself when it finish to
                                 read all the database.
        """

        Actor.__init__(self, name, level_logger, timeout)
        #: (State): Actor State.
        self.state = PullerState(Actor._initial_behaviour,
                                 SocketInterface(name, timeout),
                                 self.logger,
                                 database,
                                 report_filter,
                                 timeout, timeout_sleeping)

    def setup(self):
        """
        Define StartMessage handler and PoisonPillMessage handler
        """
        self.add_handler(PoisonPillMessage, PoisonPillMessageHandler())
        self.add_handler(StartMessage, PullerStartHandler())
        self.set_timeout_handler(TimeoutHandler())

    def terminated_behaviour(self):
        """
        Allow to end some socket connection properly
        """
        # Send kill to dispatcher
        for _, dispatcher in self.state.report_filter.filters:
            try:
                dispatcher.send_kill(by_data=True)
            except NotConnectedException:
                pass

        # Close connect to all dispatcher
        for _, dispatcher in self.state.report_filter.filters:
            dispatcher.state.socket_interface.close()

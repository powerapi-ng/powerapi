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
from powerapi.pusher import ReportHandler, PusherStartHandler, TimeoutBasicHandler, PusherPoisonPillHandler
from powerapi.message import PoisonPillMessage, StartMessage


class PusherState(State):
    """
    Pusher Actor State

    Contains in addition to State values :
      - The database interface
    """
    def __init__(self, actor, database):
        """
        :param BaseDB database: Database for saving data.
        """
        State.__init__(self, actor)

        #: (BaseDB): Database for saving data.
        self.database = database

        #: (Dict): Buffer data.
        self.buffer = []


class PusherActor(Actor):
    """
    PusherActor class

    The Pusher allow to save Report sent by Formula.
    """

    def __init__(self, name, report_type, database,
                 level_logger=logging.WARNING,
                 timeout=1000):
        """
        :param str name: Pusher name.
        :param Report report_type: Type of the report that the pusher
                                   handle.
        :param BaseDB database: Database use for saving data.
        :param int level_logger: Define the level of the logger
        """
        Actor.__init__(self, name, level_logger, timeout)

        #: (Report): Type of the report that the pusher handle.
        self.report_type = report_type

        #: (State): State of the actor.
        self.state = PusherState(self,
                                 database)

    def setup(self):
        """
        Define StartMessage, PoisonPillMessage handlers and a handler for
        each report type
        """
        self.add_handler(PoisonPillMessage, PusherPoisonPillHandler(self.state))
        self.add_handler(self.report_type, ReportHandler(self.state))
        self.add_handler(StartMessage, PusherStartHandler(self.state))
        self.set_timeout_handler(TimeoutBasicHandler(self.state))

    def teardown(self):
        """
        Allow to save the buffer before Pusher death
        """
        # Flush buffer
        if len(self.state.buffer) > 0:
            self.state.database.save_many(self.state.buffer)

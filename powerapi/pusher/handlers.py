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

import time

from powerapi.handler import InitHandler, Handler, StartHandler
from powerapi.message import ErrorMessage
from powerapi.database import DBError


class PusherStartHandler(StartHandler):
    """
    Handle Start Message
    """

    def initialization(self):
        """
        Initialize the output database
        """
        try:
            self.state.database.connect()
        except DBError as error:
            self.state.actor.send_control(ErrorMessage(error.msg))
            self.state.alive = False
            return


class ReportHandler(InitHandler):
    """
    Put the received report in a buffer

    the buffer is empty every *delay* ms or if its size exceed *max_size*

    :param int delay: number of ms before message containing in the buffer will be writen in database
    :param int max_size: maximum of message that the buffer can store before write them in database
    """

    def __init__(self, state, delay=100, max_size=50):
        InitHandler.__init__(self, state)

        self.last_database_write_time = time.time()
        self.delay = delay
        self.max_size = max_size

    def handle(self, msg):
        """
        Save the msg in the database

        :param powerapi.PowerReport msg: PowerReport to save.
        """

        self.state.buffer.append(msg)
        if (time.time() - self.last_database_write_time > self.delay) or (len(self.state.buffer) > self.max_size):
            self.state.database.save_many(self.state.buffer, self.state.report_model)
            self.state.buffer = []


class PusherPoisonPillHandler(Handler):
    """
    Set a timeout for the pusher for the timeout_handler. If he didn't
    read any input during the timeout, the actor end.
    """
    def handle(self, msg):
        """
        :param powerapi.PoisonPillMessage msg: PoisonPillMessage.
        """
        self.state.actor.set_timeout_handler(TimeoutKillHandler(self.state))
        self.state.actor.socket_interface.timeout = 2000


class TimeoutKillHandler(Handler):
    """
    Pusher timeout kill the actor
    """
    def handle(self, msg):
        """
        Kill the actor by setting alive to False
        :param msg: None
        """
        self.state.alive = False

# Copyright (C) 2018  University of Lille
# Copyright (C) 2018  INRIA
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from powerapi.handler import InitHandler, Handler, StartHandler
from powerapi.report import PowerReport
from powerapi.message import ErrorMessage
from powerapi.message import OKMessage, StartMessage
from powerapi.database import DBError


class PusherStartHandler(StartHandler):
    """
    Handle Start Message
    """

    def initialization(self, state):
        """
        Initialize the output database

        :param powerapi.State state: State of the actor.
        :rtype powerapi.State: the new state of the actor
        """
        try:
            state.database.connect()
        except DBError as error:
            state.socket_interface.send_control(ErrorMessage(error.msg))
            return state

        return state


class PowerHandler(InitHandler):
    """
    Allow to save the PowerReport received.
    """

    def handle(self, msg, state):
        """
        Save the msg in the database

        :param powerapi.PowerReport msg: PowerReport to save.
        :param powerapi.State state: State of the actor.
        """
        if not isinstance(msg, PowerReport):
            return state

        state.buffer.append(msg.serialize())

        if len(state.buffer) >= 100:
            state.database.save_many(state.buffer)
            state.buffer = []

        return state


class TimeoutHandler(InitHandler):
    """
    Pusher timeout kill the actor
    """

    def handle(self, msg, state):
        """
        Kill the actor by setting alive to False

        :param None msg: None.
        :param powerapi.State state: State of the actor.
        """
        # Flush buffer
        if len(state.buffer) > 0:
            state.database.save_many(state.buffer)

        state.alive = False
        return state

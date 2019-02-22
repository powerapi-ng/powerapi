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

from powerapi.message import OKMessage, StartMessage, ErrorMessage
from powerapi.handler import Handler


class StartHandler(Handler):
    """
    Initialize the received state
    """

    def handle(self, msg, state):
        """
        Allow to initialize the state of the actor, then reply to the control
        socket.

        :param powerapi.StartMessage msg: Message that initialize the actor
        :param powerapi.State state: State of the actor
        :rtype powerapi.State: the new state of the actor
        """
        if state.initialized:
            state.socket_interface.send_control(
                ErrorMessage('Actor already initialized'))
            return state

        if not isinstance(msg, StartMessage):
            return state

        state = self.initialization(state)

        state.initialized = True
        state.socket_interface.send_control(OKMessage())

        return state

    def initialization(self, state):
        """
        Abstract method that initialize the actor after receiving a start msg

        :param powerapi.State state: State of the actor
        :rtype powerapi.State: the new state of the actor
        """
        return state

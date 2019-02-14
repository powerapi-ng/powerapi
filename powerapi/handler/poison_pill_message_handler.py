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

from powerapi.handler import Handler
from powerapi.message import UnknowMessageTypeException, PoisonPillMessage


class PoisonPillMessageHandler(Handler):
    """
    Generic handler for PoisonPillMessage
    """

    def handle(self, msg, state):
        """
        Set the :attr:`alive <powerapi.actor.state.State.alive>`
        attribute of the actor state to False

        :param Object msg: the message received by the actor
        :param state: The current actor's state
        :type state: powerapi.actor.state.State

        :return: The new actor's state
        :rtype: powerapi.actor.state.State
        """
        if not isinstance(msg, PoisonPillMessage):
            raise UnknowMessageTypeException(type(msg))

        state.alive = False
        return state

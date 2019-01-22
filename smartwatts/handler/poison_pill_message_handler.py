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

from smartwatts.handler import Handler
from smartwatts.message import UnknowMessageTypeException, PoisonPillMessage


class PoisonPillMessageHandler(Handler):
    """
    Generic handler for PoisonPillMessage
    """

    def handle(self, msg, state):
        """
        Set the :attr:`alive <smartwatts.actor.state.BasicState.alive>`
        attribute of the actor state to False

        :param Object msg: the message received by the actor
        :param state: The current actor's state
        :type state: smartwatts.actor.state.BasicState

        :return: The new actor's state
        :rtype: smartwatts.actor.state.BasicState
        """
        if not isinstance(msg, PoisonPillMessage):
            raise UnknowMessageTypeException(type(msg))

        state.alive = False
        return state

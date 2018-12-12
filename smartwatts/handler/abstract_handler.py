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

"""
Handler interface
"""


class AbstractHandler:
    """ Handler interface """

    def handle_message(self, msg, state):
        """ Handle a message and return a the new state value of the actor

        if the given state is not initialized, return the given state without
        side effect. Otherwise, use the handle method to handle the message

        Parameters:
            msg(Object): the message received by the actor
            state(BasicState): The current actor's state

        Return:
            (BasicState): The new actor's state
        """
        if not state.initialized:
            return state

        return self.handle(msg, state)

    def handle(self, msg, state):
        """ Handle a message and return a the new state value of the actor

        Parameters:
            msg(Object): the message received by the actor
            state(BasicState): The current actor's state

        Return:
            (BasicState): The new actor's state
        """
        raise NotImplementedError()

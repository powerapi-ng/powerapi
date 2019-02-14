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


class HandlerException(Exception):
    """
    Exception raised when a problem appear in a handler
    """
    def __init__(self, msg):
        """
        :param str msg: Message of the error
        """
        super().__init__(msg)


class Handler:
    """
    Class that handle a message of a given type
    """

    def handle_message(self, msg, state):
        """
        Handle a message and return a the new state value of the actor

        This is the method that should be called to handle received message
        this method call :meth:`Handler.handle <powerapi.handler.abstract_handler.Handler.handle>`

        :param Object msg: the message received by the actor
        :param state: The current actor's state
        :type state: powerapi.actor.state.State

        :return: The new actor's state
        :rtype: powerapi.actor.state.State
        """
        return self.handle(msg, state)

    def handle(self, msg, state):
        """
        Handle a message and return a the new state value of the actor

        Override this method to implement the handler behaviour

        :param Object msg: the message received by the actor
        :param state: The current actor's state
        :type state: powerapi.actor.state.State

        :return: The new actor's state
        :rtype: powerapi.actor.state.State
        """
        raise NotImplementedError()


class InitHandler(Handler):
    """
    Class that handle a message of a given type if the actor is initialized
    """

    def handle_message(self, msg, state):
        """
        Handle a message and return a the new state value of the actor

        This is the method that should be called to handle received message

        if the given state is not initialized, return the given state without
        side effect. Otherwise, use the
        :meth:`Handler.handle <powerapi.handler.abstract_handler.Handler.handle>`
        method to handle the message

        :param Object msg: the message received by the actor
        :param state: The current actor's state
        :type state: powerapi.actor.state.State

        :return: The new actor's state
        :rtype: powerapi.actor.state.State
        """
        if not state.initialized:
            return state

        return self.handle(msg, state)

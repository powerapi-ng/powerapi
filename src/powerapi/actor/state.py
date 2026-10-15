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

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from powerapi.actor.message import Message
from powerapi.actor.supervisor import Supervisor

if TYPE_CHECKING:
    from powerapi.actor.handler import Handler


class State:
    """
    Base actor state.
    """

    def __init__(self, actor):
        """
        Initialize the actor state.
        :param actor: The actor instance
        """
        self.actor = actor

        self.initialized = False
        self.alive = True

        self.handlers: dict[type[Message], Handler] = {}
        self.supervisor = Supervisor()

        self._resolved_handlers: dict[type[Message], Handler] = {}

    def initialize(self) -> None:
        """
        Initialize resources after the actor receives a start message.
        """

    def teardown(self) -> None:
        """
        Release resources before the actor stops.
        """

    def get_corresponding_handler(self, msg: Message) -> Handler:
        """
        Return the most specific registered handler, caching successful lookups.
        :param msg: The message
        :return: The handler for the given message type
        :raises KeyError: If the message type does not have a corresponding handler
        """
        message_type = type(msg)
        try:
            return self._resolved_handlers[message_type]
        except KeyError:
            return self._resolve_handler(message_type)

    def _resolve_handler(self, message_type: type[Message]) -> Handler:
        """
        Resolve a handler in method resolution order and cache the successful lookup.
        :param message_type: The message class to resolve
        :return: The most specific registered handler
        :raises KeyError: If no handler is registered for the class or its bases
        """
        for base in message_type.__mro__:
            handler = self.handlers.get(base)
            if handler is not None:
                self._resolved_handlers[message_type] = handler
                return handler

        raise KeyError(message_type)

    def add_handler(self, message_type: type[Message], handler: Handler) -> None:
        """
        Register a handler for a message class and its subclasses.
        Exact registrations take precedence over base classes in method resolution order.
        Registering the same class again replaces its handler.
        Every registration clears the handler resolution cache.
        :param message_type: The message type
        :param handler: The corresponding handler
        """
        self.handlers[message_type] = handler
        self._resolved_handlers.clear()

    def handle_message(self, msg: Message) -> None:
        """
        Handle a message using its registered handler.
        :param msg: Message to handle
        """
        try:
            handler = self.get_corresponding_handler(msg)
        except KeyError:
            logging.warning("Unknown message type: %s", msg)
            return

        handler.handle_message(msg)

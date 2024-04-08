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

from powerapi.actor.supervisor import Supervisor
from powerapi.exception import UnknownMessageTypeException
from powerapi.handler import Handler
from powerapi.message import Message


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

        self.handlers = {}
        self.supervisor = Supervisor()

    def get_corresponding_handler(self, msg: Message) -> Handler:
        """
        Return the corresponding handler for the given message type.
        :param msg: The message
        :return: The handler for the given message type
        :raises UnknownMessageTypeException: If the message type does not have a corresponding handler
        """
        try:
            return self.handlers[msg.__class__.__name__]
        except ValueError as e:
            raise UnknownMessageTypeException() from e

    def add_handler(self, message_type: type[Message], handler: Handler, include_subclasses: bool = True):
        """
        Add a handler for the given message type.
        :param message_type: The message type
        :param handler: The corresponding handler
        :param include_subclasses: Whether to include subclasses of the message type
        """
        self.handlers[message_type.__name__] = handler

        if include_subclasses:
            for child_type in message_type.__subclasses__():
                self.handlers[child_type.__name__] = handler

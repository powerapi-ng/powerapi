# Copyright (c) 2026, Inria
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

from typing import TYPE_CHECKING

from .message import (
    ErrorMessage,
    Message,
    OKMessage,
    PoisonPillMessage,
    StartMessage,
)

if TYPE_CHECKING:
    from .state import State


class Handler[MessageT: Message]:
    """
    Handle messages using an actor state.
    """

    def __init__(self, state: State):
        """
        Initialize a message handler.
        :param state: Actor state used to handle messages
        """
        self.state = state

    def handle_message(self, msg: MessageT) -> None:
        """
        Handle a message.
        :param msg: Message to handle
        """
        self.handle(msg)

    def handle(self, msg: MessageT) -> None:
        """
        Implement the message-specific behavior.
        :param msg: Message to handle
        """
        raise NotImplementedError()


class InitializedStateHandler[MessageT: Message](Handler[MessageT]):
    """
    Handle messages only after the actor state has been initialized.
    """

    def handle_message(self, msg: MessageT) -> None:
        """
        Handle a message if the actor state is initialized.
        :param msg: Message to handle
        """
        if self.state.initialized:
            self.handle(msg)


class StartMessageHandler(Handler[StartMessage]):
    """
    Initialize an actor state in response to a start message.
    """

    def handle(self, msg: StartMessage) -> None:
        """
        Initialize the actor state and acknowledge successful initialization.
        :param msg: Start message
        """
        if self.state.initialized:
            self.state.actor.send_control(ErrorMessage('Actor already initialized'))
            return

        self.state.initialize()

        if self.state.alive:
            self.state.initialized = True
            self.state.actor.send_control(OKMessage())


class PoisonPillMessageHandler(Handler[PoisonPillMessage]):
    """
    Shut an actor down in response to a poison-pill message.
    """

    def handle(self, msg: PoisonPillMessage) -> None:
        """
        Drain pending messages when requested and stop the actor state.
        :param msg: Poison-pill message
        """
        if msg.is_soft:
            while (pending_msg := self.state.actor.socket_interface.receive(timeout=100)) is not None:
                self.state.dispatch_message(pending_msg)

        self.state.teardown(graceful=msg.is_soft)
        self.state.alive = False

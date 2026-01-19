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

from powerapi.actor.message import PoisonPillMessage
from .handler import Handler


class PoisonPillMessageHandler(Handler):
    """
    Handler responsible for shutting down an actor in response to a PoisonPillMessage.
    """

    def teardown(self, soft: bool = False) -> None:
        """
        Perform cleanup actions before the actor is stopped.
        Subclasses may override this method to release resources or perform other shutdown-related tasks.
        :param soft: Whether the shutdown is graceful (True) or immediate (False).
        """

    def handle(self, msg: PoisonPillMessage) -> None:
        """
        Trigger the shutdown of the actor.
        Pending messages will be processed before shutting down the actor if the graceful flag is enabled.
        :param msg: Message received by the actor
        """
        if msg.is_soft:
            while (msg := self.state.actor.socket_interface.receive(timeout=100)) is not None:
                self.handle_message(msg)

        self.teardown(soft=msg.is_soft)
        self.state.alive = False

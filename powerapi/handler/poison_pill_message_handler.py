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

from powerapi.handler import Handler, HandlerException
from powerapi.message import UnknowMessageTypeException, PoisonPillMessage


class PoisonPillMessageHandler(Handler):
    """
    Generic handler for PoisonPillMessage
    """

    def teardown(self):
        """
        function called before terminating the actor process
        could be redefined
        """

    def handle_msg(self, msg):
        try:
            handler = self.state.get_corresponding_handler(msg)
            handler.handle_message(msg)
        except UnknowMessageTypeException:
            self.state.actor.logger.warning("UnknowMessageTypeException: " + str(msg))
        except HandlerException:
            self.state.actor.logger.warning("HandlerException")

    def _empty_mail_box(self):
        while True:
            self.state.actor.socket_interface.timeout = 0.1
            msg = self.state.actor.socket_interface.receive()

            if msg is not None:
                self.handle_msg(msg)
            else:
                return

    def handle(self, msg):
        """
        Set the :attr:`alive <powerapi.actor.state.State.alive>`
        attribute of the actor state to False

        :param Object msg: the message received by the actor
        """
        if not isinstance(msg, PoisonPillMessage):
            raise UnknowMessageTypeException(type(msg))

        if msg.is_soft:
            self._empty_mail_box()
        self.teardown()

        self.state.alive = False

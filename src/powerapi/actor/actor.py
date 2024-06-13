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

import logging
from multiprocessing import Process
from signal import signal, Signals, SIGINT, SIGTERM

from setproctitle import setproctitle

from powerapi.exception import UnknownMessageTypeException
from powerapi.handler import HandlerException, Handler
from powerapi.message import PoisonPillMessage, Message
from .socket_interface import SocketInterface
from .state import State


class Actor(Process):
    """
    Actor class.
    An actor is started in its own process and handles messages according to its set handlers.
    """

    def __init__(self, name: str, level_logger: int = logging.WARNING, recv_timeout: int = None):
        """
        :param name: Name of the actor. (should be unique)
        :param level_logger: Define the level of the logger.
        :param recv_timeout: Define the timeout for receiving messages. (None will block indefinitely)
        """
        super().__init__(name=name)

        self.level_logger = level_logger

        self.socket_interface = SocketInterface(name)
        self.recv_timeout = recv_timeout

        self.state = State(self)
        self.logger = logging.getLogger(self.name)

    def __repr__(self):
        return f"{self.__class__.__name__}('{self.name}')"

    def _setup_logger(self):
        """
        Set up the actor logger.
        """
        self.logger.setLevel(self.level_logger)

        log_format = '%(asctime)s || %(levelname)s || %(process)d %(processName)s || %(name)s || %(message)s'
        formatter = logging.Formatter(log_format)

        handler = logging.StreamHandler()
        handler.setFormatter(formatter)

        self.logger.addHandler(handler)

    def _setup_signals_handler(self):
        """
        Define how to handle signals interrupt.
        """

        def term_handler(signum, _):
            signame = Signals(signum).name
            self.logger.debug("Received signal %s (%s), terminating actor...", signame, signum)
            self.state.alive = False

        signal(SIGTERM, term_handler)
        signal(SIGINT, term_handler)

    def _internal_setup(self):
        """
        Define the steps to initialize the actor.
        This method handles "behind the scene" steps to bring the actor up.
        """
        self._setup_logger()
        self.logger.debug('Starting actor "%s" process', self.name)

        setproctitle(repr(self))
        self._setup_signals_handler()
        self.socket_interface.setup()

        # Actor-specific setup (can be overridden)
        self.setup()

    def setup(self):
        """
        Define the steps to initialize the actor.
        """

    def _internal_teardown(self):
        """
        Define the steps to teardown the actor.
        This method handles "behind the scene" steps to bring the actor down.
        """
        self.logger.debug('Tearing down actor "%s" process', self.name)

        self.socket_interface.close()

        # Actor-specific teardown (can be overridden)
        self.teardown()

    def teardown(self):
        """
        Define the steps to teardown the actor.
        """

    def handle_received_message(self):
        """
        Handle messages received by the actor.
        """
        msg = self.receive()
        if msg is None:
            return

        try:
            self.state.get_corresponding_handler(msg).handle_message(msg)
        except UnknownMessageTypeException:
            self.logger.warning("Received unknown message type: %s", msg)
        except HandlerException:
            self.logger.warning("Failed to handle message: %s", msg)

    def run(self):
        """
        Main code executed by the actor.
        """
        self._internal_setup()

        while self.state.alive:
            self.handle_received_message()

        self._internal_teardown()

    def add_handler(self, message_type: type[Message], handler: Handler):
        """
        Add a message handler for the given message type.
        :param message_type: Type of the message.
        :param handler: Handler to use for the given message type.
        """
        self.state.add_handler(message_type, handler)

    def connect_control(self):
        """
        Connect to the control channel of the actor.
        An actor can only have one control channel open at the same time.
        """
        self.socket_interface.connect_control()

    def send_control(self, msg: Message):
        """
        Send a message to the control channel of the actor.
        :param msg: Message to send.
        """
        self.socket_interface.send_control(msg)
        self.logger.debug('Send control to actor "%s" : %s', self.name, msg)

    def receive_control(self, timeout: int = None) -> Message:
        """
        Receive a message from the control channel of the actor.
        :param timeout: Timeout in seconds.
        """
        msg = self.socket_interface.receive_control(timeout)
        self.logger.debug('Actor "%s" received control: %s', self.name, msg)
        return msg

    def connect_data(self):
        """
        Connect to the data channel of the actor.
        """
        self.socket_interface.connect_data()

    def send_data(self, msg: Message):
        """
        Send a message to the data channel of the actor.
        :param msg: Message to send.
        """
        self.socket_interface.send_data(msg)
        self.logger.debug('Send data to actor "%s": %s ', self.name, msg)

    def receive(self, timeout: int | None = None) -> Message:
        """
        Receive a message from either the control channel or the data channel of the actor.
        This call blocks until a message is received or the timeout is reached.
        """
        msg = self.socket_interface.receive(timeout)
        self.logger.debug('Actor "%s" received message: %s', self.name, msg)
        return msg

    def soft_kill(self):
        """
        Send a soft kill signal to the actor.
        """
        self.send_control(PoisonPillMessage(soft=True, sender_name='system'))

    def hard_kill(self):
        """
        Send a hard kill signal to the actor.
        """
        self.send_control(PoisonPillMessage(soft=False, sender_name='system'))

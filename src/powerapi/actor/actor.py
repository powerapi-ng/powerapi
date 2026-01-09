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
import multiprocessing
import signal
import sys
import traceback
from typing import TYPE_CHECKING

import setproctitle

from powerapi.actor.message import PoisonPillMessage
from powerapi.exception import PowerAPIExceptionWithMessage, UnknownMessageTypeException
from powerapi.handler import HandlerException
from .socket_interface import SocketInterface
from .state import State

if TYPE_CHECKING:
    from powerapi.actor.message import Message
    from powerapi.handler import Handler


class InitializationException(PowerAPIExceptionWithMessage):
    """
    Exception raised when an actor failed to initialize itself
    """


class Actor(multiprocessing.Process):
    """
    Abstract class that exposes an interface to create, setup and handle actors

    :Method Interface:

    This table list from which interface each methods are accessible

    +---------------------------------+--------------------------------------------------------------------------------------------+
    |  Interface type                 |                                   method name                                              |
    +=================================+============================================================================================+
    | Client interface                | :meth:`connect_data <powerapi.actor.actor.Actor.connect_data>`                             |
    |                                 +--------------------------------------------------------------------------------------------+
    |                                 | :meth:`connect_control <powerapi.actor.actor.Actor.connect_control>`                       |
    |                                 +--------------------------------------------------------------------------------------------+
    |                                 | :meth:`send_control <powerapi.actor.actor.Actor.send_control>`                             |
    |                                 +--------------------------------------------------------------------------------------------+
    |                                 | :meth:`send_data <powerapi.actor.actor.Actor.send_data>`                                   |
    +---------------------------------+--------------------------------------------------------------------------------------------+
    | Server interface                | :meth:`setup <powerapi.actor.actor.Actor.setup>`                                           |
    |                                 +--------------------------------------------------------------------------------------------+
    |                                 | :meth:`add_handler <powerapi.actor.actor.Actor.add_handler>`                               |
    +---------------------------------+--------------------------------------------------------------------------------------------+

    :Attributes Interface:

    This table list from wich interface each attributes are accessible

    +---------------------------------+--------------------------------------------------------------------------------------------+
    |  Interface type                 |                                   method name                                              |
    +---------------------------------+--------------------------------------------------------------------------------------------+
    | Server interface                | :attr:`state <powerapi.actor.actor.Actor.state>`                                           |
    +---------------------------------+--------------------------------------------------------------------------------------------+
    """

    def __init__(self, name, level_logger=logging.WARNING, timeout=None):
        """
        Initialization and start of the process.

        :param str name: unique name that will be used to indentify the actor
                         processus
        :param int level_logger: Define the level of the logger
        :param int timeout: if defined, do something if no msg is recv every
                            timeout (in ms)
        """
        multiprocessing.Process.__init__(self, name=name)

        #: (logging.Logger): Logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level_logger)
        formatter = logging.Formatter(
            '%(asctime)s || %(levelname)s || ' +
            '%(process)d %(processName)s || %(message)s')
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        #: (powerapi.State): Actor context
        self.state: State | None = None

        #: (powerapi.SocketInterface): Actor's SocketInterface
        self.socket_interface = SocketInterface(name, timeout)

        #: (List): list of exception that restart the actor it they are raised
        self.low_exception = []

    def run(self):
        """
        Main code executed by the actor
        """
        self._setup_actor()

        while self.state.alive:
            try:
                self._process_received_messages()
            except Exception as exn:
                if type(exn) in self.low_exception:
                    self.logger.error('Minor exception raised, restart actor !')
                    traceback.print_exc()
                else:
                    self.state.alive = False
                    self.logger.error('Major Exception raised, stop actor')
                    traceback.print_exc()

        self._teardown_actor()

    def _signal_handler_setup(self):
        """
        Define how to handle signal interrupts
        """

        def term_handler(signum, _):
            signame = signal.Signals(signum).name
            self.logger.debug("Received signal %s (%s), terminating actor...", signame, signum)

            msg = PoisonPillMessage(soft=False)
            handler = self.state.get_corresponding_handler(msg)
            handler.handle(msg)

            self._teardown_actor()
            sys.exit(0)

        signal.signal(signal.SIGTERM, term_handler)
        signal.signal(signal.SIGINT, term_handler)

    def _setup_actor(self):
        """
        Internal initialization routine executed by the actor before starting to process messages.
        """
        setproctitle.setproctitle(self.name)
        self.socket_interface.setup()
        self._signal_handler_setup()

        self.setup()

        self.logger.debug('Actor "%s" process created', self.name)

    def setup(self):
        """
        Initializes the actor before it begins processing messages.
        Override this method to customize the actor’s initialization logic.
        You **must** initialize the actor’s state within this method.
        """
        self.state = State(self)

    def add_handler(self, message_type: type[Message], handler: Handler):
        """
        Map a handler to a message type

        :param type message_type: type of the message that the handler can
                                  handle
        :param handler: handler that will handle all messages of the given type
        :type handler: powerapi.handler.Handler
        """
        self.state.add_handler(message_type, handler)

    def _process_received_messages(self):
        """
        Process the messages received by the actor.
        """
        msg = self.socket_interface.receive()
        self.logger.debug('Received message: %s', msg)
        if msg is None:
            return  # Timeout

        try:
            handler = self.state.get_corresponding_handler(msg)
            handler.handle_message(msg)
        except UnknownMessageTypeException:
            self.logger.warning("Unknown message type: %s", msg)
        except HandlerException:
            self.logger.warning("Failed to handle message: %s", msg)

    def _teardown_actor(self):
        """
        Internal teardown routine executed by the actor before it stops.
        """
        self.teardown()
        self.socket_interface.close()
        self.logger.debug('Actor "%s" teardown', self.name)

    def teardown(self):
        """
        Cleanup method executed in the actor process before it shuts down.
        Override this method to customize the actor’s cleanup logic.
        """

    def send_control(self, msg: Message) -> None:
        """
        Send a message on the control channel of the actor.
        Used internally to respond to control messages received from other actors.
        :param msg: Message to send
        """
        self.socket_interface.send_control(msg)
        self.logger.debug('Sent control message: %s', msg)

    def get_proxy(self, connect_control: bool = False, connect_data: bool = False) -> ActorProxy:
        """
        Returns a proxy object for this actor.
        The proxy object is used to communicate with the actor via its IPC interface.
        :param connect_control: Whether to connect to the actor control channel
        :param connect_data: Whether to connect to the actor data channel
        :return: Proxy object
        """
        proxy = ActorProxy(self.name, self.__class__)

        if connect_control:
            proxy.connect_control()

        if connect_data:
            proxy.connect_data()

        return proxy


class ActorProxy:
    """
    Proxy object for actors.
    Used to communicate with an actor via its IPC interface.
    """

    def __init__(self, actor_name: str, actor_type: type[Actor]):
        """
        Initialize a new actor proxy object.
        :param actor_name: Name of the actor
        :param actor_type: Type of the actor
        """
        self.actor_name = actor_name
        self.actor_type = actor_type

        self._ipc_interface = SocketInterface(actor_name, None)

    def connect_control(self) -> None:
        """
        Connect to the actor's control channel.
        """
        self._ipc_interface.connect_control()

    def send_control(self, msg: Message) -> None:
        """
        Sends a message to the actor's control channel.
        :param msg: Message to send
        """
        self._ipc_interface.send_control(msg)

    def receive_control(self, timeout: int | None = None) -> Message:
        """
        Receive a message from the actor's control channel.
        :param timeout: Timeout in seconds, None blocks indefinitely
        :return: The received message
        """
        return self._ipc_interface.receive_control(timeout)

    def connect_data(self) -> None:
        """
        Connect to the actor's data channel.
        """
        self._ipc_interface.connect_data()

    def send_data(self, msg: Message) -> None:
        """
        Sends a message to the actor's data channel.
        :param msg: Message to send
        """
        self._ipc_interface.send_data(msg)

    def kill(self, graceful: bool = True) -> None:
        """
        Sends a kill message to the actor.
        :param graceful: If true, the actor will process its pending messages before stopping; If false, stop immediately.
        """
        self.send_control(PoisonPillMessage(soft=graceful))

    def disconnect(self) -> None:
        """
        Disconnect from the control and data channels of the actor.
        """
        self._ipc_interface.close()

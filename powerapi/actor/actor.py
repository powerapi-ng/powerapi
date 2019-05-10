"""
Copyright (c) 2018, INRIA
Copyright (c) 2018, University of Lille
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import logging
import signal
import multiprocessing
import setproctitle
import sys

import zmq

from powerapi.actor import State, SocketInterface
from powerapi.message import PoisonPillMessage
from powerapi.message import UnknowMessageTypeException
from powerapi.handler import HandlerException


class Actor(multiprocessing.Process):
    """
    Abstract class that exposes an interface to create, setup and handle actors

    :Method Interface:

    This table list from wich interface each methods are accessible

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
    |                                 +--------------------------------------------------------------------------------------------+
    |                                 | :meth:`send_kill <powerapi.actor.actor.Actor.send_kill>`                                   |
    +---------------------------------+--------------------------------------------------------------------------------------------+
    | Server interface                | :meth:`setup <powerapi.actor.actor.Actor.setup>`                                           |
    |                                 +--------------------------------------------------------------------------------------------+
    |                                 | :meth:`add_handler <powerapi.actor.actor.Actor.add_handler>`                               |
    |                                 +--------------------------------------------------------------------------------------------+
    |                                 | :meth:`teardown <powerapi.actor.actor.Actor.teardown>`                                     |
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
        :param int timeout: if define, do something if no msg is recv every
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

        # file logger
        #handlerf = logging.FileHandler('powerapi.log')
        #handlerf.setLevel(level_logger)
        #handlerf.setFormatter(formatter)

        self.logger.addHandler(handler)
        #self.logger.addHandler(handlerf)

        #: (powerapi.State): Actor context
        self.state = State(self)

        #: (powerapi.SocketInterface): Actor's SocketInterface
        self.socket_interface = SocketInterface(name, timeout)

        #: (func): Actor behaviour
        self.behaviour = Actor._initial_behaviour

    def run(self):
        """
        Main code executed by the actor
        """
        self._setup()

        while self.state.alive:
            self.behaviour(self)

        self._kill_process()

    def _signal_handler_setup(self):
        """
        Define how to handle signal interrupts
        """
        def term_handler(_, __):
            self.logger.info("Term handler")
            self._kill_process()
            sys.exit(0)

        signal.signal(signal.SIGTERM, term_handler)
        signal.signal(signal.SIGINT, term_handler)

    def _setup(self):
        """
        Set actor specific configuration:

         - set the processus name
         - setup the socket interface
         - setup the signal handler

        This method is called before entering on the behaviour loop
        """
        # Name process
        setproctitle.setproctitle(self.name)

        self.socket_interface.setup()

        self.logger.info(self.name + ' process created.')

        self._signal_handler_setup()

        self.setup()

    def setup(self):
        """
        Function called before entering on the behaviour loop

        Can be overriden to use personal actor setup
        """

    def add_handler(self, message_type, handler):
        """
        Map a handler to a message type

        :param type message_type: type of the message that the handler can
                                  handle
        :param handler: handler that will handle all messages of the given type
        :type handler: powerapi.handler.Handler
        """
        self.state.add_handler(message_type, handler)

    def set_behaviour(self, new_behaviour):
        """
        Set a new behaviour
        :param new_behaviour: function
        """
        self.behaviour = new_behaviour

    def _initial_behaviour(self):
        """
        Initial behaviour of an actor

        Wait for a message, and handle it with the correct handler

        If the message is None, call the timout_handler otherwise find the
        handler correponding to the message type and call it on the message.
        """
        msg = self.receive()

        # Timeout
        if msg is None:
            self.state.timeout_handler.handle_message(None)
        # Message
        else:
            try:
                handler = self.state.get_corresponding_handler(msg)
                handler.handle_message(msg)
            except UnknowMessageTypeException:
                self.logger.warning("UnknowMessageTypeException: " +
                                    str(msg))
            except HandlerException:
                self.logger.warning("HandlerException")

    def _kill_process(self):
        """
        Kill the actor (close sockets)
        """
        self.teardown()
        self.socket_interface.close()
        self.logger.info(self.name + " teardown")

    def set_timeout_handler(self, new_timeout_handler):
        """
        Set the timeout_handler
        """
        self.state.timeout_handler = new_timeout_handler

    def teardown(self):
        """
        Function called before closing sockets

        Can be overriden to use personal actor termination behaviour
        """

    def connect_data(self):
        """
        Open a canal that can be use for unidirectional communication to this
        actor
        """
        self.socket_interface.connect_data()

    def set_context(self, context):
        """
        set the context of the actor
        :param zmq.Context context: the context to set
        """
        self.socket_interface.set_context(context)

    def connect_control(self):
        """
        Open a control canal with this actor. An actor can have only one
        control open at the same time. Open a pair socket on the process
        that want to control this actor
        """
        self.socket_interface.connect_control()

    def send_control(self, msg):
        """
        Send a message to this actor on the control canal

        :param Object msg: the message to send to this actor
        """
        self.socket_interface.send_control(msg)
        self.logger.info('send control [' + str(msg) + '] to ' + self.name)

    def receive_control(self, timeout=None):
        """
        Receive a message from this actor on the control canal
        """
        if timeout is None:
            timeout = self.socket_interface.timeout

        msg = self.socket_interface.receive_control(timeout)
        self.logger.info("receive control : [" + str(msg) + "]")
        return msg

    def send_data(self, msg):
        """
        Send a msg to this actor using the data canal

        :param Object msg: the message to send to this actor
        """
        self.socket_interface.send_data(msg)
        self.logger.info('send data [' + str(msg) + '] to ' + self.name)

    def receive(self):
        """
        Block until a message was received (or until timeout) an return the
        received messages

        :return: the list of received messages or an empty list if timeout
        :rtype: a list of Object
        """
        msg = self.socket_interface.receive()
        self.logger.info("receive data : [" + str(msg) + "]")
        return msg

    def send_kill(self, by_data=False):
        """
        Kill this actor by sending a
        :class:`PoisonPillMessage
        <powerapi.message.message.PoisonPillMessage>`

        :param bool by_data: Define if the kill msg is send in the control
                             socket or the data socket
        """
        if by_data:
            self.send_data(PoisonPillMessage())
        else:
            self.send_control(PoisonPillMessage())
        self.socket_interface.close()

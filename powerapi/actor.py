# Copyright (c) 2021, INRIA
# Copyright (c) 2021, University of Lille
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.

# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.

# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.

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

from typing import Any, Type
from datetime import timedelta

from thespian.actors import ActorTypeDispatcher, ActorAddress, ActorExitRequest, WakeupMessage

from powerapi.message import PingMessage, OKMessage, ErrorMessage, StartMessage
from powerapi.exception import PowerAPIExceptionWithMessage, PowerAPIException


class InitializationException(PowerAPIExceptionWithMessage):
    """
    Exception raised when an actor failed to initialize itself
    """


class ActorNotInitializedException(PowerAPIException):
    """
    Exception raised when a non initialized actor received a message that is not a StartMessage
    """


class Actor(ActorTypeDispatcher):
    """
    PowerAPI Actor Abstract Class
    """
    def __init__(self, start_message_cls: Type[StartMessage]):
        """
        This method must be used only in a daughter class constructor

        :param start_message_cls: Type of the message that will be used to initialize the actor
        """
        ActorTypeDispatcher.__init__(self)
        self.name: str = 'no_name_yet'
        self.parent: ActorAddress = None
        self.initialized: bool = False
        self.start_message_cls = start_message_cls

    def log_critical(self, message: str):
        """
        send a critical message to the log actor
        """
        extra_args = {'actor_name': self.name}
        logging.critical(message, extra=extra_args)

    def log_error(self, message: str):
        """
        send an error message to the log actor
        """
        extra_args = {'actor_name': self.name}
        logging.error(message, extra=extra_args)

    def log_warning(self, message: str):
        """
        send a warning message to the log actor
        """
        extra_args = {'actor_name': self.name}
        logging.warning(message, extra=extra_args)

    def log_info(self, message: str):
        """
        send an information message to the log actor
        """
        extra_args = {'actor_name': self.name}
        logging.info(message, extra=extra_args)

    def log_debug(self, message: str):
        """
        send a debug message to the log actor
        """
        extra_args = {'actor_name': self.name}
        logging.debug(message, extra=extra_args)

    def receiveMsg_PingMessage(self, message: PingMessage, sender: ActorAddress):
        """
        When receiving a PingMessage, the actor answer with a OKMessage to its sender
        """
        self.log_debug('received message ' + str(message))
        self.send(sender, OKMessage(self.name))

    def receiveMsg_StartMessage(self, message: StartMessage, sender: ActorAddress):
        """
        When receiving a StartMessage :
          - if the actor is already initialized, answer with a ErrorMessage
          - otherwise initialize the actor with the abstract method _initialization and answer with an OKMessage
        """
        self.name = message.name
        self.log_debug('received message ' + str(message))
        self.parent = sender

        if self.initialized:
            self.send(sender, ErrorMessage(self.name, 'Actor already initialized'))
            return

        if not isinstance(message, self.start_message_cls):
            self.send(sender, ErrorMessage(self.name, 'use ' + self.start_message_cls.__name__ + ' instead of StartMessage'))
            return

        try:
            self._initialization(message)
        except InitializationException as exn:
            self.send(sender, ErrorMessage(self.name, exn.msg))
            self.send(self.myAddress, ActorExitRequest())
            return

        self.initialized = True
        self.send(sender, OKMessage(self.name))
        self.log_info(self.name + ' started')

    def receiveMsg_ErrorMessage(self, message: ErrorMessage, _: ActorAddress):
        """
        When receiving an error message send it to the log actor
        """
        self.log_error(str(message.error_message))

    def receiveUnrecognizedMessage(self, message: Any, sender: ActorAddress):
        """
        When receiving a message with a type that can't be handle, the actor answer with an ErrorMessage
        """
        self.log_warning('received unrecognized message : ' + str(message))
        self.send(sender, ErrorMessage(self.name, "did not recognize the message type : " + str(type(message))))

    def receiveMsg_ActorExitRequest(self, message: ActorExitRequest, _: ActorAddress):
        """
        When receive ActorExitRequestMessage log it and exit
        """
        self.log_debug('received message ' + str(message))
        self.log_info(self.name + ' exit')

    def _initialization(self, start_message: StartMessage):
        pass


class TimedActor(Actor):
    """
    An actor that process a task at regular time interval
    """

    def __init__(self, start_message_cls, time_interval: float):
        """
        :param time_interval: time (in seconds) to wait between each task to launch
        """
        Actor.__init__(self, start_message_cls)
        self._time_interval = timedelta(seconds=time_interval)

    def receiveMsg_StartMessage(self, message: StartMessage, sender: ActorAddress):
        """
        When receiving a StartMessage, initialize the actor and set it into sleeping phase
        ask the actor system to wake agter a given time period
        """
        Actor.receiveMsg_StartMessage(self, message, sender)
        self.wakeupAfter(self._time_interval)

    def receiveMsg_WakeupMessage(self, _: WakeupMessage, __: ActorAddress):
        """
        When receiving a WakeupMessage, launch the actor task
        """
        if self.initialized:
            self._launch_task()
        else:
            self.log_error('received a wakeup message without being initialized before')
            raise ActorNotInitializedException()

    def _launch_task(self):
        raise NotImplementedError()

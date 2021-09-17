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
import sys

from typing import Type

from thespian.actors import ActorSystem

from powerapi.message import OKMessage, ErrorMessage, StartMessage, EndMessage
from powerapi.actor import InitializationException, Actor
from powerapi.exception import PowerAPIExceptionWithMessage
from powerapi.pusher import PusherActor
from powerapi.puller import PullerActor
from powerapi.dispatcher import DispatcherActor


class ActorCrashedException(PowerAPIExceptionWithMessage):
    """
    Exception raised when an actor crashed and can't be restarted
    """


class ActorLogFilter(logging.Filter):
    """
    Log filter
    """
    def filter(self, record):
        """
        filter logs that was produced by actor
        """
        return 'actor_name' in record.__dict__


class NotActorLogFilter(logging.Filter):
    """
    Log filter
    """
    def filter(self, record):
        """
        filter logs that was not produced by actor
        """
        return 'actorAddress' not in record.__dict__


LOG_DEF = {
    'version': 1,
    'formatters': {
        'normal': {'format': '%(levelname)s::%(created)s::ROOT::%(message)s'},
        'actor': {'format': '%(levelname)s::%(created)s::%(actor_name)s::%(message)s'}},
    'filters': {
        'isActorLog': {'()': ActorLogFilter},
        'notActorLog': {'()': NotActorLogFilter}},
    'handlers': {
        'h1': {'class': 'logging.StreamHandler',
               'stream': sys.stdout,
               'formatter': 'normal',
               'filters': ['notActorLog'],
               'level': logging.DEBUG},
        'h2': {
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'formatter': 'actor',
            'filters': ['isActorLog'],
            'level': logging.DEBUG}
    },
    'loggers': {'': {'handlers': ['h1', 'h2'], 'level': logging.DEBUG}}
}


class Supervisor:
    """
    Interface with Actor system
    Used to launch, stop and monitor actors
    """
    def __init__(self, verbose_mode: bool):
        """
        :param verbose_mode: Specify the log level : True -> DEBUG False -> INFO
        """
        if verbose_mode:
            LOG_DEF['handlers']['h1']['level'] = logging.DEBUG
            LOG_DEF['handlers']['h2']['level'] = logging.DEBUG
        else:
            LOG_DEF['handlers']['h1']['level'] = logging.INFO
            LOG_DEF['handlers']['h2']['level'] = logging.INFO

        self.system = ActorSystem(systemBase='multiprocQueueBase', logDefs=LOG_DEF)
        self.pushers = {}
        self.pullers = {}
        self.dispatchers = {}
        self.actors = {}

    def launch(self, actor_cls: Type[Actor], start_message: StartMessage):
        """
        create an actor from a given class and send it a start message.
        :param actor_cls: class used to create the actor
        :param start_message: message used to initialize the actor
        :raise InitializationException: if an error occurs during actor initialiszation process
        """
        name = start_message.name
        address = self.system.createActor(actor_cls)
        answer = self.system.ask(address, start_message)

        if isinstance(answer, OKMessage):
            self._add_actor(address, name, actor_cls)
            logging.info('launch %s actor', name)
            return address
        elif isinstance(answer, ErrorMessage):
            raise InitializationException(answer.error_message)
        raise InitializationException("Unknow message type : " + str(type(answer)))

    def _add_actor(self, address, name, actor_cls):
        if issubclass(actor_cls, PusherActor):
            self.pushers[name] = address
        elif issubclass(actor_cls, PullerActor):
            self.pullers[name] = address
        elif issubclass(actor_cls, DispatcherActor):
            self.dispatchers[name] = address
        else:
            raise AttributeError('Actor is not a DispatcherActor, PusherActor or PullerActor')
        self.actors[name] = address

    def _wait_actors(self):
        for _ in self.pushers:
            self.system.listen()

    def shutdown(self):
        """
        Shutdown the entire actor system and all the actors
        """
        self.system.shutdown()

    def monitor(self):
        """
        wait for an actor to send an EndMessage or for an actor to crash
        """
        while True:
            msg = self.system.listen(1)
            if msg is None:
                pass
            elif isinstance(msg, EndMessage):
                self._wait_actors()
                return
            else:
                logging.error("Unknow message type : %s", str(type(msg)))

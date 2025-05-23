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

import multiprocessing

from powerapi.exception import PowerAPIException
from powerapi.message import StartMessage, ErrorMessage


class ActorInitError(PowerAPIException):
    """
    Exception raised when an error occuried during the actor initialisation
    process
    """

    def __init__(self, message):
        super().__init__()

        #: (str): error description
        self.message = message


class FailConfigureError(PowerAPIException):
    """
    Exception raised when an error occured during the actor setup process
    """


class CrashConfigureError(PowerAPIException):
    """
    Exception raised when an actor crash during initialisation
    """


class ActorAlreadySupervisedException(PowerAPIException):
    """
    Exception raised when trying to supervise with a supervisor that already
    supervise this actor
    """


class ActorAlreadyLaunchedException(PowerAPIException):
    """
    Exception raised when trying to supervise with a supervisor that already
    supervise this actor
    """


SUPERVISOR_NAME = 'powerapi_supervisor'


class Supervisor:
    """
    Provide basic functionality to deal with actors: launch and kill
    """

    def __init__(self):
        #: ([powerapi.actor.actor.Actor]): list of supervised actors
        self.supervised_actors = []

    def launch_actor(self, actor, start_message=True):
        """
        Launch the actor :
          - start the process that execute the actor code
          - connect the data and control socket
          - send a StartMessage to initialize the actor if needed

        :param Actor actor: Actor to be launched
        :param boolean start_message: True a StartMessage need to be sent to
                                     this actor

        :raise: zmq.error.ZMQError if a communication error occurs
        :raise: powerapi.actor.ActorInitError if the actor crash during the
                initialisation process
        """
        if actor.is_alive():
            raise ActorAlreadyLaunchedException()

        actor.start()
        actor.connect_control()
        actor.connect_data()

        if start_message:
            actor.send_control(StartMessage())
            msg = actor.receive_control(2000)
            if isinstance(msg, ErrorMessage):
                raise ActorInitError(msg.error_message)

            if msg is None:
                if actor.is_alive():
                    actor.terminate()
                    raise FailConfigureError(f'Unable to configure the actor: {actor.name}')
                raise CrashConfigureError(f'The actor "{actor.name}" crashed during initialisation')

        self.supervised_actors.append(actor)

    def join(self):
        """
        wait until all actor are terminated
        """
        actor_sentinels = [actor.sentinel for actor in self.supervised_actors]
        multiprocessing.connection.wait(actor_sentinels)

    def kill_actors(self, soft=False):
        """
        Kill all the supervised actors
        """
        for actor in self.supervised_actors:
            if actor.is_alive():
                if soft:
                    actor.soft_kill()
                else:
                    actor.hard_kill()
                actor.join()

    def are_all_actors_alive(self) -> bool:
        """
        Identify if one of the actors is dead
        :return: True if all the actors are alive
        """
        for actor in self.supervised_actors:
            if not actor.is_alive():
                return False
        return True

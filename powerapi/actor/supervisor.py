# Copyright (C) 2018  University of Lille
# Copyright (C) 2018  INRIA
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from powerapi.message import StartMessage, ErrorMessage


class ActorInitError(Exception):
    """
    Exception raised when an error occuried during the actor initialisation
    process
    """
    def __init__(self, message):
        Exception.__init__(self)

        #: (str): error description
        self.message = message


class ActorAlreadySupervisedException(Exception):
    """
    Exception raised when trying to supervise with a supervisor that already
    supervise this actor
    """


class ActorAlreadyLaunchedException(Exception):
    """
    Exception raised when trying to supervise with a supervisor that already
    supervise this actor
    """


class Supervisor:

    def __init__(self):
        #: ([powerapi.actor.actor.Actor]): list of supervised actors
        self.supervised_actors = []

    def launch_actor(self, actor, start_message=True):
        """
        Launch the actor :
          - start the process that execute the actor code
          - connect the data and control socket
          - send a StartMessage to initialize the actor if needed

        :param boolean startMessage: True a StartMessage need to be sent to
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
            msg = actor.receive_control(500)
            if isinstance(msg, ErrorMessage):
                raise ActorInitError(msg.error_message)
            elif msg is None:
                if actor.is_alive():
                    actor.terminate()
                    raise ActorInitError('Unable to configure the actor')
                else:
                    raise ActorInitError(
                        'The actor crash during initialisation process')
        self.supervised_actors.append(actor)

    def join(self):
        """
        wait until all actor are terminated
        """
        for actor in self.supervised_actors:
            actor.join()

    def kill_actors(self, by_data=False):
        """
        Kill all the supervised actors

        :param bool by_data: Define if the kill msg is send in the control
                             socket or the data socket
        """
        for actor in self.supervised_actors:
            if actor.is_alive():
                actor.send_kill(by_data=by_data)
                actor.join()

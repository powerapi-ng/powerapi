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

"""
Module class PusherActor
"""

from smartwatts.actor import Actor, BasicState, SocketInterface
from smartwatts.pusher import PowerHandler, StartHandler
from smartwatts.message import PoisonPillMessage, StartMessage
from smartwatts.handler import PoisonPillMessageHandler


class PusherState(BasicState):
    """ Pusher Actor State

    Contains in addition to BasicState values :
      - the database interface
    """
    def __init__(self, behaviour, socket_interface, database):
        BasicState.__init__(self, behaviour, socket_interface)
        self.database = database


class PusherActor(Actor):
    """ PusherActor class """

    def __init__(self, name, report_type, database, verbose=False):
        Actor.__init__(self, name, verbose)
        self.report_type = report_type
        self.state = PusherState(PusherActor._initial_behaviour,
                                 SocketInterface(name, 3000), database)

    def setup(self):
        """
        Define StartMessage, PoisonPillMessage handlers and a handler for
        each report type
        """
        Actor.setup(self)
        self.add_handler(PoisonPillMessage, PoisonPillMessageHandler())
        self.add_handler(self.report_type, PowerHandler())
        self.add_handler(StartMessage, StartHandler())

    def _initial_behaviour(self):
        """
        Override

        Initial behaviour of Pusher actor

        wait for a message, and handle it with the correct handler
        if the message is None, call the timout_handler otherwise find the
        handler correponding to the message type and call it on the message.
        """
        msg_list = self.state.socket_interface.receive()
        self.log('received : ' + str(msg_list))

        # Timeout
        if msg_list == []:
            self.state.alive = False
        else:
            for msg in msg_list:
                handler = self.get_corresponding_handler(msg)
                self.state = handler.handle_message(msg, self.state)
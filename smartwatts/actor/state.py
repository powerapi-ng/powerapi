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


class BasicState:
    """
    A basic state class that encapsulate basic actor values :

    :attr:`initialized <smartwatts.actor.state.BasicState.initialized>`
    :attr:`alive <smartwatts.actor.state.BasicState.alive>`
    :attr:`behaviour <smartwatts.actor.state.BasicState.behaviour>`
    :attr:`socket_interface <smartwatts.actor.state.BasicState.socket_interface>`
    """

    def __init__(self, behaviour, socket_interface):
        """
        :param behaviour: function that implement the basic behaviour
        :type behaviour: (fun (actor) -> None)
        :param socket_interface: communication interface of the actor
        :type socket_interface: smartwatts.actor.socket_interface.SocketInterface
        """

        #: (bool): True if the actor is initialized and can handle all
        #: message, False otherwise
        self.initialized = False
        #: (bool): True if the actor is alive, False otherwise
        self.alive = True
        #: (smartwatts.SocketInterface): Communication interface of the actor
        self.socket_interface = socket_interface
        #: (func): Function that implement the current behaviour
        self.behaviour = behaviour

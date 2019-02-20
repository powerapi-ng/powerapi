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
Module test_actor_pusher
"""

import mock
import zmq
from powerapi.database import MongoDB
from powerapi.filter import Filter
from powerapi.report import Report
from powerapi.pusher import PusherActor, PusherStartHandler, PowerHandler
from powerapi.pusher import PusherState
from powerapi.actor import State, Actor, SocketInterface
from powerapi.report import HWPCReport, PowerReport
from powerapi.message import StartMessage, OKMessage, ErrorMessage

##############################################################################


def get_fake_mongodb():
    """ Return a fake MongoDB """
    fake_mongo = mock.Mock(spec_set=MongoDB)
    values = [2, 3]

    def fake_next():
        if not values:
            return None
        return values.pop()

    def fake_iter():
        return iter([])

    fake_mongo.__next__ = fake_next
    fake_mongo.__iter__ = fake_iter
    return fake_mongo


def get_fake_socket_interface():
    """ Return a fake SockerInterface """
    return mock.Mock(spec_set=SocketInterface)


##############################################################################


class TestHandlerPusher:
    """ TestHandlerPusher class """

    def test_pusher_start_handler(self):
        """
        Test the StartHandler of PusherActor
        """

        # Define PusherState
        fake_database = get_fake_mongodb()
        fake_socket_interface = get_fake_socket_interface()
        pusher_state = PusherState(Actor._initial_behaviour,
                                   fake_socket_interface,
                                   fake_database,
                                   mock.Mock())
        assert pusher_state.initialized is False

        # Define StartHandler
        start_handler = PusherStartHandler()

        # Test Random message when state is not initialized
        to_send = [OKMessage(), ErrorMessage("Error"),
                   HWPCReport("test", "test", "test")]
        for msg in to_send:
            start_handler.handle(msg, pusher_state)
            assert fake_database.method_calls == []
            assert fake_socket_interface.method_calls == []
            assert pusher_state.initialized is False

        # Try to initialize the state
        start_handler.handle(StartMessage(), pusher_state)
        assert pusher_state.initialized is True


    def test_pusher_power_handler(self):
        """
        Test the PowerHandler of PusherActor
        """
        
        # Define PusherState
        fake_database = get_fake_mongodb()
        fake_socket_interface = get_fake_socket_interface()
        pusher_state = PusherState(Actor._initial_behaviour,
                                   fake_socket_interface,
                                   fake_database,
                                   mock.Mock())
        assert pusher_state.initialized is False

        # Define PowerHandler
        power_handler = PowerHandler()
        
        # Test Random message when state is not initialized
        to_send = [OKMessage(), ErrorMessage("Error"),
                   HWPCReport("test", "test", "test")]
        for msg in to_send:
            power_handler.handle(msg, pusher_state)
            assert pusher_state.database.method_calls == []
            assert pusher_state.initialized is False

        pusher_state.initialized = True

        # Test Random message when state is initialized
        to_send = [OKMessage(), ErrorMessage("Error"),
                   HWPCReport("test", "test", "test")]
        for msg in to_send:
            power_handler.handle(msg, pusher_state)
            assert pusher_state.database.method_calls == []

        # Test with a PowerMessage
        power_handler.handle(PowerReport("10", "test", "test", "test", "test"),
                             pusher_state)
        assert pusher_state.database.method_calls != []
